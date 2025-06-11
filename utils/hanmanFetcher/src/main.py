from AikanhanmanFetcher import AikanhanmanFetcher
from HanmankuFetcher import HanmankuFetcher
from KamuFetcher import KamuFetcher
from WuwuhanmanFetcher import WuwuhanmanFetcher
import os
import json
import logging
import sys
from ConfigHandler import ConfigHandler

gFetcherMapping = {
    'hmk': {
        'name': '韩漫库',
        'host': 'se8.us',
        'fetcher': HanmankuFetcher
    },
    'akhm': {
        'name': '爱看韩漫',
        'host': 'www.aikanhanman.com',
        'fetcher': AikanhanmanFetcher
    },
    'kamu': {
        'name': '卡慕漫画',
        'host': 'kamu.cc',
        'fetcher': KamuFetcher
    },
    'wuwu': {
        'name': '污污漫画',
        'host': 'www.comicbox.xyz',
        'fetcher': WuwuhanmanFetcher
    }
}
gLogger = None
selfDir = os.path.dirname(os.path.abspath(__file__))
configPath = "%s/../config/config.json" % selfDir
configHandler = ConfigHandler(configPath)


def initLogger():
    global gLogger
    selfDir = os.path.dirname(os.path.abspath(__file__))
    logFilePath = ("%s/../log/log.log" % (selfDir))
    FORMAT = '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
    DATEFMT = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(filename = logFilePath, level = logging.INFO, format = FORMAT, datefmt = DATEFMT)
    gLogger = logging.getLogger('main')


def getLogger():
    return gLogger


def getLinkAndChapterIdxMappings(fetcherKey, comicList):
    retList = []
    for comicInfo in comicList:
        entry = {'link': '', 'idx': 0, 'name': ''}
        if 'latestChapterIdx' in comicInfo.keys():
            entry['idx'] = comicInfo['latestChapterIdx']
        if 'name' in comicInfo.keys():
            entry['name'] = comicInfo['name']
        if 'links' in comicInfo.keys() and fetcherKey in comicInfo['links'].keys() and comicInfo['links'][fetcherKey] != '':
            entry['link'] = comicInfo['links'][fetcherKey]
            retList.append(entry)
    return retList


def updateAllComics():
    jsonConfig = configHandler.getConfig()
    comicRootPath = jsonConfig['targetDir']
    comicList = jsonConfig['comics']
    for key in gFetcherMapping.keys():
        if key != 'wuwu':
            pass
        fetcherClass = gFetcherMapping[key]['fetcher']
        fetcher = fetcherClass(comicRootPath, gFetcherMapping[key]['name'])
        linkAndIdxMappings = getLinkAndChapterIdxMappings(key, comicList)
        for entry in linkAndIdxMappings:
            fetcher.setInternalParameters(entry['link'], entry['name'], entry['idx'])
            fetcher.fetchComic()
            newLatestIdx = fetcher.getLatestChapterIdx()
            comicName = fetcher.getComicName()
            if newLatestIdx > entry['idx']:
                #print("%d --> %d" % (entry['idx'], newLatestIdx))
                configHandler.updateLatestChapterIdx(key, entry['link'], comicName, newLatestIdx)
                #for c in jsonConfig['comics']:
                #    for link in c['links'].values():
                #        if link == entry['link']:
                #            print("In jsonConfig after update: %d" % c['latestChapterIdx'])



if __name__ == '__main__':
    initLogger()
    if not configHandler.validateConfig():
        exit(1)
    if len(sys.argv) == 1:
        updateAllComics()
    if len(sys.argv) == 2:
        link = sys.argv[-1]
        foundKey = ''
        for key in gFetcherMapping:
            if link.find(gFetcherMapping[key]['host']) >= 0:
                foundKey = key
                break
        if foundKey != '':
            configHandler.insertNewComic(key, link)
