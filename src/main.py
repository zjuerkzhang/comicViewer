# -*- coding: utf-8 -*-
# filename: main.py
import web
from dirPage import dirPage
from dirContentFetcher import dirContentFetcher
from imageFetcher import imageFetcher
from kwpPage import kwpPage
from wsgiref.simple_server import make_server, WSGIRequestHandler

class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass  # 什么都不做，抑制所有请求日志

urls = (
    '/kwp/(.*)', 'kwpPage',
    '/', 'dirPage',
    '/content', 'dirContentFetcher',
    '/image/(.+)', 'imageFetcher',
    '/(.+)/', 'dirPage',
    '/(.+)/content', 'dirContentFetcher'
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    server = make_server('', 9001, app.wsgifunc(), handler_class=QuietHandler)
    print("Running on http://localhost:9001")
    server.serve_forever()
