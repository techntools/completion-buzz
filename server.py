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


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    workspaces = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspaces = {}

    def completions(self, msg):
        wid = msg.get('wid', None)

        if wid is None:
            return "What ?"

        if 'closing' in msg:
            del self.workspaces[wid]
            return []

        engine = self.workspaces.get(wid, None)

        if engine is None:
            engine = CompletionEngine()
            self.workspaces[wid] = engine

        if 'target' in msg:
            bufferkeywords = msg.get('bufferkeywords', [])
            if len(bufferkeywords) > 0:
                if isinstance(bufferkeywords[0], dict):
                    bufferkeywords = []
                    for bk in msg['bufferkeywords']:
                        bufferkeywords.append([*bk.values()][0])

            return engine.findmatches(
                msg['target'],
                set(bufferkeywords + engine.wordpool + msg.get('tagcompletions', [])),
            )
        else:
            # Note: Keywords start with albhabets, _, $ only for programming languages.
            keywordpattern = r'[$\w_]+'

            if 'filelist' in msg:
                engine.update_words_per_file(keywordpattern, msg['filelist'])

            if 'filelines' in msg and 'fileloc' in msg:
                engine.update_words_of_file(
                    keywordpattern,
                    msg['fileloc'],
                    '\n'.join(msg['filelines'])
                )

            return f'WID is {wid}'

    def handle(self):
        while True:
            try:
                data = self.request.recv(1024 * 1024 * 5).decode('utf-8')
                if data == '':
                    break

                decoded = json.loads(data)

                # Send a response if the sequence number is positive.
                # Negative numbers are used for "eval" responses.
                if decoded[0] >= 0:
                    response = self.completions(json.loads(decoded[1]))

                    id = decoded[0]

                    encoded = json.dumps([id, response])

                    self.request.sendall(encoded.encode('utf-8'))
            except ValueError:
                response = "JSON decoding failed"
                encoded = json.dumps([-1, response])
                self.request.sendall(encoded.encode('utf-8'))
            except socket.error:
                break


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
