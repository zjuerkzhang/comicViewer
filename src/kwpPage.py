# -*- coding: utf-8 -*-
# filename: kwpPage.py

import web
import os
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

def prepareImagePageInfo(pageInfo, dirPath, dirContent, imgFilename):
    currentIdx = 0
    if imgFilename != '':
        currentIdx = dirContent['files'].index(imgFilename)
    nextIdx = currentIdx + 1
    if nextIdx >= len(dirContent['files']):
        nextIdx = currentIdx
    pageInfo['imgs']['currentHref'] = '/comic/image/%s/%s' % (dirPath, dirContent['files'][currentIdx])
    pageInfo['imgs']['nextHref'] = '/comic/kwp/%s/%s' % (dirPath, dirContent['files'][nextIdx])
    return pageInfo

def prepareDirPageInfo(pageInfo, dirPath, dirContent):
    colLimit = 3
    dirs = dirContent['dirs']
    if len(dirs) % colLimit == 0:
        rowLen = int(len(dirs) / colLimit)
    else:
        rowLen = int(len(dirs) / colLimit) + 1
    for rIdx in range(rowLen):
        row = []
        for cIdx in [0, 1, 2]:
            dirIdx = rIdx * colLimit + cIdx
            if dirIdx >= len(dirs):
                col = {
                    'href': '',
                    'title': ''
                }
            else:
                col = {
                    'href': "/comic/kwp%s/%s/" % (dirPath, dirs[dirIdx]),
                    'title': dirs[dirIdx]
                }
            row.append(col)
        pageInfo['dirs']['rows'].append(row)
    return pageInfo

class kwpPage(object):
    def GET(self, path = '/'):
        '''
        path =  /some/dir/ or
                /some/image/file.jpg
        '''
        pageInfo = {
            'title': '',
            'upperHref': '',
            'dirs': {
                'rows': []
            },
            'imgs': {
                'currentHref': '',
                'nextHref': ''
            }
        }
        path = '/' + path
        if path[-1] != '/' and (not fileEndWithWantedExtention(path)):
            return "Invalid directory path: [%s]" % path

        urlDir = '/'.join(path.split('/')[:-1])
        fileSystemDir = '%s%s' % (g_root_dir, urlDir)
        if not os.path.exists(fileSystemDir):
            return "Invalid directory path!"
        fileList = os.listdir(fileSystemDir)
        dirContent = {'dirs': [], 'files': []}
        for f in fileList:
            if fileContainWantedPrefix(f):
                continue
            if os.path.isdir(fileSystemDir + '/' + f):
                dirContent['dirs'].append(f)
            else:
                if fileEndWithWantedExtention(f):
                    dirContent['files'].append(f)
        dirContent['dirs'].sort()
        dirContent['files'].sort()
        render = web.template.render(self_dir + '/../templates')
        if urlDir == '/':
            pageInfo['title'] = 'Comic'
        else:
            pageInfo['title'] = urlDir.split('/')[-1]
            pageInfo['upperHref'] = "/comic/kwp" + '/'.join(path.split('/')[:-2]) + '/'

        if fileEndWithWantedExtention(path) or len(dirContent['files']) > 0:
            pageInfo = prepareImagePageInfo(pageInfo, urlDir, dirContent, path.split('/')[-1])
            return render.kwpImgPage(pageInfo)
        else:
            pageInfo = prepareDirPageInfo(pageInfo, urlDir, dirContent)
            return render.kwpDirPage(pageInfo)

