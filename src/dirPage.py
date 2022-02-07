# -*- coding: utf-8 -*-
# filename: dirPage.py

import web
import os

self_dir = os.path.dirname(os.path.abspath(__file__))
g_root_dir = self_dir + "/../comic/"

class dirPage(object):
    def GET(self, path = ''):
        fileList = os.listdir(g_root_dir)
        dirName = path.split('/')[-1]
        pageInfo = {
            'title': dirName if dirName != '' else 'Index',
            'relativePath': path.replace('/', '-')
            }
        render = web.template.render(self_dir + '/../templates')
        return render.page(pageInfo)
