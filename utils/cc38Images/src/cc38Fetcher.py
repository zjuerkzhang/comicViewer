# -*- coding: utf-8 -*-
import sys
import requests
from bs4 import BeautifulSoup as bs
import logging
import re
import os
import json

selfDir = os.path.dirname(os.path.abspath(__file__))
fileName = '.'.join(__file__.split('.')[:-1]).split('/')[-1]
logFilePath = ("%s/../../log/log.log" % (selfDir))
FORMAT = '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename = logFilePath, level = logging.INFO, format = FORMAT, datefmt = DATEFMT)

logger = logging.getLogger(fileName)
host = "www.38cc.cc"
site = "http://" + host
targetRootDir = "%s/../images/" % selfDir
configFilePath = "%s/../config/config.json" % selfDir
notificationUrl="https://bloghz.ddns.net/cmd/notify/"

requestSession = requests.Session()
imgSession = requests.Session()

def getValidSoupFromLink(link):
    r = requestSession.get(link)
    if r.status_code != 200:
        logger.error("Fail to fetch content from [%s]" % link)
        return None
    soup = bs(r.text, 'html5lib')
    if soup == None:
        logger.error("Fail to parse content from [%s]" % link)
    return soup

def downloadImg(imgUrl, targetImgPath):
    logger.debug("Download: %s --> %s" % (imgUrl, targetImgPath))
    downloadSuccess = False
    with open(targetImgPath, 'wb') as f:
        r = imgSession.get(imgUrl)
        if r.status_code != 200:
            logger.error("Fail to fetch image from [%s]" % imgUrl)
        else:
            downloadSuccess = True
            f.write(r.content)
    return downloadSuccess


def fetchImagesFromSubPage(subPageLink, chapterIdx, chapterDir):
    logger.debug("subPageLink: [%s], chapterId: [%d]" % (subPageLink, chapterIdx))
    url = subPageLink if subPageLink.find(site) == 0 else ( "http://" + subPageLink if subPageLink.find(host) == 0 else (site + subPageLink) )
    soup = getValidSoupFromLink(url)
    if soup == None:
        return False
    contentDiv = soup.find('div', attrs = {'id': 'content'})
    if contentDiv == None:
        logger.error("Fail to get <div id='content'> from [%s]" % subPageLink)
        return False
    imgs = contentDiv.find_all('img')
    if len(imgs) == 0:
        logger.error("No <img> in <div id='content'> found [%s]" % subPageLink)
        return False
    logger.info("[%d] <img> in <div id='content'> found [%s]" % (len(imgs), subPageLink))
    imgIdx = 1
    for img in imgs:
        imgExt = img['src'].split('.')[-1]
        targetImgPath = chapterDir + ("%03d.%s" % (imgIdx, imgExt))
        ret = downloadImg(img['src'], targetImgPath)
        imgIdx = imgIdx + 1
    return True

def getComicNameFromSoup(soup):
    h1 = soup.find('h1')
    if h1 == None:
        logger.info("Fail to get <h1> from soup")
        return ''
    return h1.string

def fetchComic(link, configData = {}):
    resultJson = {
            'name': '',
            'link': link,
            'latestChapterIdx': 0
        }
    if len(configData.keys()) > 0:
        resultJson['name'] = configData['name']
        resultJson['latestChapterIdx'] = configData['latestChapterIdx']
    lastChapterIdx = resultJson['latestChapterIdx']

    soup = getValidSoupFromLink(link)
    if resultJson['name'] == '':
        resultJson['name'] = getComicNameFromSoup(soup)
    comicDir = targetRootDir + resultJson['name'] + '/'
    if not os.path.exists(comicDir):
        os.mkdir(comicDir)

    listDiv = soup.find('div', attrs = {'id': 'list'})
    if listDiv == None:
        logger.error("Fail to get <div id='list'> from [%s]" % link)
        return resultJson
    dds = listDiv.find_all('dd')
    if len(dds) == 0:
        logger.error("No <dd> in <div id='list'> found")
        return resultJson
    subPages = {}
    for dd in dds:
        a = dd.find('a')
        if a == None:
            logger.info("No <a> under <dd> [%s]" % dd.prettify())
        chapterIdx = int(re.findall('\d+', a.string)[0])
        subPages[chapterIdx] = a['href']
    logger.info("Get total [%d] sub-pages" % len(subPages.keys()))
    for chapterIdx in sorted(subPages.keys()):
        if chapterIdx > lastChapterIdx:
            chapterDir = comicDir + ("%03d/" % chapterIdx)
            if not os.path.exists(chapterDir):
                os.mkdir(chapterDir)
            ret = fetchImagesFromSubPage(subPages[chapterIdx], chapterIdx, chapterDir)
            if ret:
                resultJson['latestChapterIdx'] = chapterIdx
            else:
                break
    return resultJson



if __name__ == "__main__":
    if len(sys.argv) == 1:
        # load config.json to update the latest
        logger.info("===== Try to update to fetch the lastest chapters =====")
        if not os.path.exists(configFilePath):
            logger.info("No configuration file found")
            exit(1)
        with open(configFilePath, 'r') as f:
            jsonConfig = json.load(f)
        if 'comics' not in jsonConfig.keys():
            logger.info("No comic to update")
            exit(1)
        configFileNeedUpdate = False
        notifMsg = ""
        for comicConfigData in jsonConfig['comics']:
            logger.info("----- Comic [%s] -----" % comicConfigData['name'])
            retData = fetchComic(comicConfigData['link'], comicConfigData)
            if retData['latestChapterIdx'] > comicConfigData['latestChapterIdx']:
                msg = "Comic [%s] is updated from [%d] to [%d]" % (comicConfigData['name'], comicConfigData['latestChapterIdx'], retData['latestChapterIdx'])
                logger.info(msg)
                notifMsg = notifMsg + msg + '\n'
                comicConfigData['latestChapterIdx'] = retData['latestChapterIdx']
                configFileNeedUpdate = True
            else:
                logger.info("No update for Comic [%s], still in [%d]" % (comicConfigData['name'], comicConfigData['latestChapterIdx']))
        if configFileNeedUpdate:
            jsonMsg = {
                'subject': 'XTWITTER: 38CC',
                'channel': 'telegram',
                'content': " - " + notifMsg
            }
            requests.post(notificationUrl, json = jsonMsg)
            with open(configFilePath, 'w') as f:
                json.dump(jsonConfig, f, indent = 4, ensure_ascii = False)

    elif len(sys.argv) == 2:
        comicLink = sys.argv[-1]
        logger.info("Try to fetch new comic from %s" % comicLink)
        if os.path.exists(configFilePath):
            with open(configFilePath, 'r') as f:
                jsonConfig = json.load(f)
        else:
            jsonConfig = {
                'comics': []
            }
        existingComicLinks = list(map(lambda x: x['link'], jsonConfig['comics']))
        if comicLink in existingComicLinks:
            logger.info("New comic of [%s] exists" % comicLink)
            print("New comic of [%s] exists, try to execute without link" % comicLink)
            exit(1)
        retData = fetchComic(comicLink)
        jsonConfig['comics'].append(retData)
        with open(configFilePath, 'w') as f:
            json.dump(jsonConfig, f, indent = 4, ensure_ascii = False)
    else:
        logger.error("Invalid parameter count")