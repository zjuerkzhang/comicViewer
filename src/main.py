# -*- coding: utf-8 -*-
# filename: main.py
import web
from dirPage import dirPage
from dirContentFetcher import dirContentFetcher
from imageFetcher import imageFetcher

urls = (
    '/', 'dirPage',
    '/content', 'dirContentFetcher',
    '/image/(.+)', 'imageFetcher',
    '/(.+)/', 'dirPage',
    '/(.+)/content', 'dirContentFetcher'
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
