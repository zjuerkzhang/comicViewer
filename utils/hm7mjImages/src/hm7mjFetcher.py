# -*- coding: utf-8 -*-
import sys
import requests
from bs4 import BeautifulSoup as bs
import logging
import re
import os
import json
import random
import time

selfDir = os.path.dirname(os.path.abspath(__file__))
fileName = '.'.join(__file__.split('.')[:-1]).split('/')[-1]
logFilePath = ("%s/../log/%s.log" % (selfDir, fileName))
FORMAT = '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename = logFilePath, level = logging.INFO, format = FORMAT, datefmt = DATEFMT)

logger = logging.getLogger('BasicFetcher')
host = "www.7mj.net"
site = "https://" + host
targetRootDir = "%s/../images/" % selfDir
configFilePath = "%s/../config/config.json" % selfDir
notificationUrl="https://bloghz.ddns.net/cmd/notify/"

requestSession = requests.Session()
imgSession = requests.Session()
headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-Hans-CN,zh-CN;q=0.9,zh;q=0.8,en;q=0.7,en-GB;q=0.6,en-US;q=0.5,ja;q=0.4',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.53 Safari/537.36 Edg/80.0.361.33',
            'Connection' : 'keep-alive',
            'Cache-Control': 'no-cache',
            'Host': host
        }
cookies = None

'''
API:
get chapters: https://www.7mj.net/json/chapter.php?zpid=510
get images: https://www.7mj.net/json/info.php?id=30492&type=1
'''

def getValidSoupFromLink(link):
    r = requestSession.get(link, headers= headers, cookies=cookies)
    if r.status_code != 200:
        logger.error("Fail to fetch content from [%s]" % link)
        return None
    soup = bs(r.text, 'html5lib')
    if soup == None:
        logger.error("Fail to parse content from [%s]" % link)
    return soup

def getValidJsonDataFromLink(link):
    r = requestSession.get(link, headers= headers, cookies=cookies)
    if r.status_code != 200:
        logger.error("Fail to fetch content from [%s]" % link)
        return {}
    return r.json()

def convertComicPageLinkToJsonLink(pageLink):
    comicId = pageLink.split('/comic/')[-1]
    if comicId == '' or re.match('^\d+$', comicId) == None:
        return ''
    return "https://%s/json/chapter.php?zpid=%s" % (host, comicId)

def getValidChapterJsonDataFromPageLink(link):
    jsonLink = convertComicPageLinkToJsonLink(link)
    if jsonLink == '':
        logger.error("cannot get json link from page link [%s]" % link)
        return {}
    else:
        return getValidJsonDataFromLink(jsonLink)

def getChapterJsonLink(chapterId):
    return "https://%s/json/info.php?id=%s&type=1" % (host, chapterId)

def downloadImg(imgUrl, targetImgPath):
    logger.debug("Download: %s --> %s" % (imgUrl, targetImgPath))
    content = None
    try:
        time.sleep(random.random())
        r = imgSession.get(imgUrl, verify = False, timeout=5)
        if r.status_code != 200:
            logger.error("Fail to fetch image from [%s], status_code = [%d]" % (imgUrl, r.status_code))
        else:
            content = r.content
    except:
        logger.error("Fail to download image from [%s] to [%s]" % (imgUrl, targetImgPath))
    if content == None:
        return False
    with open(targetImgPath, 'wb') as f:
        f.write(content)
    return True


def fetchImagesFromSubPage(chapterId, chapterIdx, chapterDir):
    subPageLink = getChapterJsonLink(chapterId)
    logger.debug("subPageLink: [%s], chapterId: [%d]" % (subPageLink, chapterIdx))
    imageJson = getValidJsonDataFromLink(subPageLink)
    if 'data' not in imageJson.keys():
        logger.error("No attribute 'data' in imageJson from url: [%s]" % subPageLink)
        return False
    if len(imageJson["data"]) != 1:
        logger.error("imageJson['data'] is empty list from url: [%s]" % subPageLink)
        return False
    if 'list' not in imageJson["data"][0].keys():
        logger.error("No attribute 'data' in imageJson['data'][0] from url: [%s]" % subPageLink)
        return False
    imgs = imageJson["data"][0]["list"]
    if not os.path.exists(chapterDir):
        os.mkdir(chapterDir)
    fileExistCount = len(os.listdir(chapterDir))
    if fileExistCount >= len(imgs):
        logger.info("[%d] images exist in [%s], more than image count from web [%d], no need download images" % (fileExistCount, chapterDir, len(imgs)))
        return True
    imageDledCount = 0
    for img in imgs:
        imgExt = img['img'].split('.')[-1]
        targetImgPath = chapterDir + ("%03d.%s" % (img['num'], imgExt))
        ret = downloadImg(img['img'], targetImgPath)
        if ret:
            imageDledCount = imageDledCount + 1
    return (imageDledCount == len(imgs))

def getComicNameFromSoup(soup):
    h1 = soup.find('h1')
    if h1 == None:
        logger.info("Fail to get <h1> from soup")
        return ''
    return h1.string

def login():
    global cookies
    requestSession.get("https://%s/user/loginx.php" % host, headers=headers)
    loginPostData = {
        "dopost": "login",
        "keeptime": str(3600 * 24 * 365 * 10),
        "username": "tototot@email.com",
        "password": "ia2LFEuE5utF2hg"
    }
    loginUrl = "https://%s/user/do.php?" % host
    firstPara = True
    for key in loginPostData.keys():
        if not firstPara:
            loginUrl = loginUrl + "&"
        else:
            firstPara = False
        loginUrl = loginUrl + ("%s=%s" % (key, loginPostData[key]))
    print(loginUrl)
    r = requestSession.post(loginUrl, headers= headers)
    if r.status_code != 200:
        logger.error("Fail to login [%s]" % loginUrl)
        return False
    print(r.cookies)
    cookies = r.cookies
    return True

def getChapterIds(chapterJson):
    chapterIds = {}
    if 'length' not in chapterJson.keys():
        return chapterIds
    for entry in chapterJson["length"]:
        url = entry["url"]
        chapterPageFile = url.split('/view/')[-1]
        chapterId = chapterPageFile.split('.')[0]
        if chapterId == '' or re.match('^\d+$', chapterId) == None:
            logger.error("Invalid chapter entry info due to fail to get chapter id: [%s]" % str(entry))
            continue
        if re.match('^\d+$', entry["num"]) == None:
            continue
        chapterIds[int(entry["num"])] = chapterId
    return chapterIds

def fetchComic(link, comicRootDir, comicInfo = {}):
    if len(comicInfo.keys()) == 0:
        comicInfo = {
                'name': '',
                'links': {
                    'twhm': '',
                    'yxhm': '',
                    '5wc': '',
                    '7mj': link
                },
                'latestChapterIdx': 0
            }
    lastChapterIdx = comicInfo['latestChapterIdx']

    soup = getValidSoupFromLink(link)
    if comicInfo['name'] == '':
        comicInfo['name'] = getComicNameFromSoup(soup)
    comicDir = comicRootDir + '/' + comicInfo['name'] + '/'
    if not os.path.exists(comicDir):
        os.mkdir(comicDir)

    chapterJsonData = getValidChapterJsonDataFromPageLink(link)
    subPages = getChapterIds(chapterJsonData)
    logger.info("Get total [%d] sub-pages" % len(subPages.keys()))
    for chapterIdx in sorted(subPages.keys()):
        if chapterIdx > lastChapterIdx:
            chapterDir = comicDir + ("%03d/" % chapterIdx)
            ret = fetchImagesFromSubPage(subPages[chapterIdx], chapterIdx, chapterDir)
            if ret:
                comicInfo['latestChapterIdx'] = chapterIdx
            else:
                jsonMsg = {
                    'subject': 'Caoliu topic: 乐漫网',
                    'channel': 'telegram',
                    'content': " - Fail to update chapter [%d] of [%s]" % (chapterIdx, comicInfo['name'])
                }
                requests.post(notificationUrl, json = jsonMsg)
                break
    return comicInfo

def getValidConfigContent():
    if not os.path.exists(configFilePath):
        logger.info("No configuration file found")
        return None
    with open(configFilePath, 'r') as f:
        jsonConfig = json.load(f)
    if 'targetDir' not in jsonConfig.keys():
        logger.info("No key <targetDir> exists in config.json")
        return None
    if not os.path.exists(jsonConfig['targetDir']):
        logger.info("No target directory referred by [%s]" % jsonConfig['targetDir'])
        return None
    return jsonConfig

def getValidComicInfoContent(comicInfoFilePath):
    if not os.path.exists(comicInfoFilePath):
        logger.info("No info.json under [%s], skip" % comicInfoFilePath)
        return None
    with open(comicInfoFilePath, 'r') as f:
        comicInfo = json.load(f)
    if 'links' not in comicInfo.keys() or '7mj' not in comicInfo['links'].keys():
        logger.info("No <links> or <links/7mj> in [%s] " % comicInfoFilePath)
        return None
    link = comicInfo['links']['7mj']
    if link == '':
        logger.info("No valid 7mj link in [%s] " % comicInfoFilePath)
        return None
    return comicInfo

if __name__ == "__main__":
    if not login():
        logger.error("Login Failed")
        exit(1)
    jsonConfig = getValidConfigContent()
    if jsonConfig == None:
        exit(1)
    targetDir = jsonConfig['targetDir']
    if len(sys.argv) == 1:
        # load config.json to update the latest
        logger.info("===== Try to update to fetch the lastest chapters =====")
        entryList = os.listdir(targetDir)
        comicDirList = list(filter(lambda x: os.path.isdir("%s/%s" % (targetDir, x)), entryList))

        configFileNeedUpdate = False
        notifMsg = ""
        for comicDir in comicDirList:
            comicInfoFilePath = "%s/%s/info.json" % (targetDir, comicDir)
            comicInfo = getValidComicInfoContent(comicInfoFilePath)
            if comicInfo == None:
                continue

            link = comicInfo['links']['7mj']
            latestChapterIdx = comicInfo['latestChapterIdx'] if 'latestChapterIdx' in comicInfo.keys() else 0
            name = comicInfo['name'] if 'name' in comicInfo.keys() else ''

            logger.info("----- Update Comic [%s] from chapter [%d], [%s] -----" % (name, latestChapterIdx, link))
            retData = fetchComic(link, targetDir, comicInfo)
            if retData['latestChapterIdx'] > latestChapterIdx:
                msg = "Comic [%s] is updated from [%d] to [%d]" % (retData['name'], latestChapterIdx, retData['latestChapterIdx'])
                logger.info(msg)
                notifMsg = "%s - %s\n" % (notifMsg, msg)
                comicInfo['latestChapterIdx'] = retData['latestChapterIdx']
                configFileNeedUpdate = True
                with open(comicInfoFilePath, 'w') as f:
                    json.dump(retData, f, indent = 4, ensure_ascii = False)
            else:
                logger.info("No update for Comic [%s], still in [%d]" % (retData['name'], retData['latestChapterIdx']))
        if configFileNeedUpdate:
            jsonMsg = {
                'subject': 'Caoliu topic: 乐漫网',
                'channel': 'telegram',
                'content': notifMsg
            }
            requests.post(notificationUrl, json = jsonMsg)

    elif len(sys.argv) == 2:
        comicLink = sys.argv[-1]
        logger.info("Try to fetch new comic from %s" % comicLink)
        soup = getValidSoupFromLink(comicLink)
        comicName = getComicNameFromSoup(soup)
        if comicName == '':
            print("No valid comic by [%s]" % comicLink)
            exit(1)
        comicDir = "%s/%s" % (targetDir, comicName)
        if os.path.exists(comicDir):
            print("[%s] by [%s] exists, no need manual update" % (comicName, comicLink))
            exit(0)
        retData = fetchComic(comicLink, targetDir)
        if retData['latestChapterIdx'] > 0:
            infoJsonPath = "%s/%s/info.json" % (targetDir, comicName)
            with open(infoJsonPath, 'w') as f:
                json.dump(retData, f, indent = 4, ensure_ascii = False)
    else:
        logger.error("Invalid parameter count")