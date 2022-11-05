#!/usr/bin/python3
#
# Server that will accept connections from a Vim channel.
# Run this server and then in Vim you can open the channel:
#  :let handle = ch_open('localhost:8765')
#
# Then Vim can send requests to the server:
#  :let response = ch_sendexpr(handle, 'hello!')
#
# And you can control Vim by typing a JSON message here, e.g.:
#   ["ex","echo 'hi there'"]
#
# There is no prompt, just type a line and press Enter.
# To exit cleanly type "quit<Enter>".
#
# See ":help channel-demo" in Vim.
#
# This requires Python 2.6 or later.

import json
import socket
import sys
import threading
import socketserver

from engine import CompletionEngine


thesocket = None


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    per_working_dir = {}

    def handle(self):
        print("=== socket opened ===")

        global thesocket

        thesocket = self.request

        while True:
            try:
                data = self.request.recv(4096 * 9).decode('utf-8')
            except socket.error:
                print("=== socket error ===")
                break
            if data == '':
                print("=== socket closed ===")
                break

            try:
                decoded = json.loads(data)
            except ValueError:
                print("json decoding failed")
                decoded = [-1, '']

            # Send a response if the sequence number is positive.
            # Negative numbers are used for "eval" responses.
            if decoded[0] >= 0:
                if decoded[1] == 'hello!':
                    response = "got it"
                    id = decoded[0]
                elif decoded[1] == 'hello channel!':
                    response = "got that"
                    # response is not to a specific message callback but to the
                    # channel callback, need to use ID zero
                    id = 0
                else:
                    msg = json.loads(decoded[1])
                    if 'wid' in msg:
                        wid = msg['wid']

                        if 'closing' in msg:
                            del self.per_working_dir[wid]
                            continue

                        engine = self.per_working_dir.get(wid, None)

                        if engine is None:
                            engine = CompletionEngine()
                            self.per_working_dir[wid] = engine

                        response = f'CWD is {wid}'

                        if 'target' in msg:
                            matches = engine.findmatches(msg['target'])

                            if 'tagcompletions' in msg:
                                matches = set(msg['tagcompletions']).union(matches)

                            if 'bufferkeywords' in msg:
                                matches = engine._searcher.findmatches(
                                    matches.union(msg['bufferkeywords']),
                                    msg['target']
                                )

                            response = []
                            for m in matches:
                                response.append({ 'word': m })
                        else:
                            # Note: Keywords start with albhabets, _, $ only for programming languages.
                            keywordpattern = '[a-zA-Z0-9_]+'
                            filelist = msg['filelist']
                            engine.startmining(keywordpattern, filelist)
                    else:
                        response = "What ?"

                    id = decoded[0]

                encoded = json.dumps([id, response])

                self.request.sendall(encoded.encode('utf-8'))

            print("received: {0}".format(data))
            print("Sending {0}".format(encoded))

        thesocket = None


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "localhost", 8765

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)

    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread: ", server_thread.name)

    print("Listening on port {0}".format(PORT))
    while True:
        typed = sys.stdin.readline()
        if "quit" in typed:
            print("Goodbye!")
            break
        if thesocket is None:
            print("No socket yet")
        else:
            print("Sending {0}".format(typed))
            thesocket.sendall(typed.encode('utf-8'))

    server.shutdown()
    server.server_close()
