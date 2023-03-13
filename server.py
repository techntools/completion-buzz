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
import threading
import socketserver
import daemon

from engine import CompletionEngine


thesocket = None


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    per_working_dir = {}

    def handle(self):
        # === socket opened ===

        global thesocket

        thesocket = self.request

        while True:
            try:
                data = self.request.recv(4096 * 9).decode('utf-8')
                if data == '':
                    # === socket closed ===
                    break

                decoded = json.loads(data)
                msg = json.loads(decoded[1])

                # Send a response if the sequence number is positive.
                # Negative numbers are used for "eval" responses.
                if decoded[0] >= 0:
                    if 'wid' in msg:
                        wid = msg['wid']

                        if 'closing' in msg:
                            del self.per_working_dir[wid]
                            continue

                        engine = self.per_working_dir.get(wid, None)

                        if engine is None:
                            engine = CompletionEngine()
                            self.per_working_dir[wid] = engine

                        response = f'WID is {wid}'

                        if 'target' in msg:
                            matches = engine.findmatches(msg['target'])

                            if 'tagcompletions' in msg:
                                matches = set(msg['tagcompletions']).union(matches)

                            if 'bufferkeywords' in msg:
                                matches = engine.findmatches(
                                    msg['target'],
                                    matches.union(msg['bufferkeywords']),
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
            except ValueError:
                response = "JSON decoding failed"
                encoded = json.dumps([-1, response])
                self.request.sendall(encoded.encode('utf-8'))
            except socket.error:
                # === socket error ===
                break

        thesocket = None


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    with daemon.DaemonContext():
        HOST, PORT = "localhost", 8765

        server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.start()
