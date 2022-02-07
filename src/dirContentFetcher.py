# -*- coding: utf-8 -*-
# filename: dirContentFetcher.py

from distutils import filelist
import web
import os
import json

self_dir = os.path.dirname(os.path.abspath(__file__))
g_root_dir = self_dir + "/../comic/"
skipped_file_dir_prefix = ['_']
imageExtension = ['.jpg', '.gif', '.png']

def fileContainWantedPrefix(filename, prefixes = skipped_file_dir_prefix):
    for prefix in prefixes:
        if filename.find(prefix) == 0:
            return True
    return False

def fileEndWithWantedExtention(filename, extensions = imageExtension):
    for ext in extensions:
        if filename.lower().find(ext) > 0 and (filename.lower().find(ext) + len(ext) == len(filename)):
            return True
    return False

class dirContentFetcher(object):
    def GET(self, path = ''):
        targetPath = '%s/%s/' % (g_root_dir, path)
        if not os.path.exists(targetPath):
            return "Invalid directory path!"
        fileList = os.listdir(targetPath)
        dataJson = {'dirs': [], 'files': []}
        for f in fileList:
            if fileContainWantedPrefix(f):
                continue
            if os.path.isdir(targetPath + f):
                dataJson['dirs'].append(f)
            else:
                if fileEndWithWantedExtention(f):
                    dataJson['files'].append(f)
        web.header('Content-Type', 'application/json')
        return json.dumps(dataJson)
