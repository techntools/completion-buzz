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

from engine import CompletionEngine


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    workspaces = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspaces = {}

    def completions(self, msg):
        # Adding defensive if for checking wid is ok but would just add to
        # delay. Client should make sure that wid is passed. Otherwise use
        # default workspace. But it will include words from every workspace
        # which will add up to more delay.
        wid = msg.get('wid', 'workspace')

        try:
            engine = self.workspaces[wid]

            if 'target' in msg:
                return engine.findmatches(
                    msg['target'],
                    set(msg.get('bufferkeywords', []) + engine.wordpool + msg.get('tagcompletions', [])),
                    msg['skip'],
                )

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

            if 'closing' in msg:
                del self.workspaces[wid]
                return []
        except KeyError as ke:
            if ke.args[0] == wid:
                self.workspaces[wid] = CompletionEngine()
        except Exception as e:
            raise e

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
    HOST, PORT = "localhost", 8765

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
