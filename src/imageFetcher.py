# -*- coding: utf-8 -*-
# filename: imageFetcher.py

import web
import os

self_dir = os.path.dirname(os.path.abspath(__file__))
g_root_dir = self_dir + "/../comic/"

class imageFetcher(object):
    def GET(self, imagePath = ''):
        #print(imagePath)
        targetImgPath = '%s/%s' % (g_root_dir, imagePath)
        #print(targetImgPath)
        if not os.path.exists(targetImgPath):
            raise web.notfound()
        imageBinary = open(targetImgPath,'rb').read()
        return imageBinary