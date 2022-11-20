# -*- coding: utf-8 -*-
# filename: dirContentFetcher.py

import web
import os
import json
import re

self_dir = os.path.dirname(os.path.abspath(__file__))
g_root_dir = self_dir + "/../comic/"
skipped_file_dir_prefix = ['_']
imageExtension = ['.jpg', '.gif', '.png', 'jpeg']

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
        dataJson = {'dirs': [], 'files': [], 'nextChapter': ''}
        for f in fileList:
            if fileContainWantedPrefix(f):
                continue
            if os.path.isdir(targetPath + f):
                dataJson['dirs'].append(f)
            else:
                if fileEndWithWantedExtention(f):
                    dataJson['files'].append(f)
        print(targetPath)
        if re.search('/\d{3}/$', targetPath) != None or re.search('/\d{3}-\d{3}/$', targetPath) != None:
            currentDir = targetPath.split('/')[-2]
            parentPath = targetPath.replace('%s/' % currentDir, '')
            brotherDirs = list(filter(lambda x:os.path.isdir(parentPath + x), os.listdir(parentPath)))
            brotherDirs.sort()
            currentIdx = brotherDirs.index(currentDir)
            if currentIdx == len(brotherDirs) - 1:
                dataJson['nextChapter'] = '../'
            else:
                dataJson['nextChapter'] = '../%s/' %  brotherDirs[currentIdx + 1]
        web.header('Content-Type', 'application/json')
        return json.dumps(dataJson)
