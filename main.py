import os
import json
from time import sleep
from http.server import BaseHTTPRequestHandler, HTTPServer

import bot.handlers.__main__
from bot.bot import bot

from telebot import types


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # ###### # <--- Gets the data itself
        body = json.loads(post_data.decode())

        bot.process_new_updates([types.Update.de_json(body)])

        self.send_response(204)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'')
        return


PORT = int(os.environ.get('PORT'))
if not PORT or PORT not in (80, 88, 443, 8443):
    PORT = 8443

httpd = HTTPServer(('', PORT), handler)
print('Starting httpd...\n')
sleep(1)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
httpd.server_close()
print('Stopping httpd...\n')
