import os

import json
from time import sleep
from http.server import BaseHTTPRequestHandler, HTTPServer

import bot.handlers.__main__
from bot.bot import bot

from telebot import types


class handler(BaseHTTPRequestHandler):
    server_version = 'WebhookHandler/1.0'

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        bot.remove_webhook()
        bot.set_webhook(url='https://xo-telegram-bot.herokuapp.com/' + bot.token)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Webhook set')

    def do_DELETE(self):
        bot.remove_webhook()

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Webhook deleted')

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


if __name__ == '__main__':
    httpd = HTTPServer(('', int(os.environ.get('PORT', 5000))), handler)
    print('Starting httpd...\n')
    sleep(1)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('Stopping httpd...\n')
