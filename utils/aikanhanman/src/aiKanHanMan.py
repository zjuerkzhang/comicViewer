# -*- coding: utf-8 -*-
import sys
import requests
from bs4 import BeautifulSoup as bs
import logging
import re
import os
import json
import time
import random

selfDir = os.path.dirname(os.path.abspath(__file__))
fileName = '.'.join(__file__.split('.')[:-1]).split('/')[-1]
logFilePath = ("%s/../../log/log.log" % (selfDir))
FORMAT = '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename = logFilePath, level = logging.INFO, format = FORMAT, datefmt = DATEFMT)

logger = logging.getLogger(fileName)
host = "www.aikanhanman.com"
site = "https://" + host
configFilePath = "%s/../config/config.json" % selfDir
notificationUrl="https://bloghz.ddns.net/cmd/notify/"

gProxies = {
    'http': 'http://127.0.0.1:8080',
    'https': 'http://127.0.0.1:8080'
}
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
imgHeaders = {
            'Accept': 'image/avif,image/webp,*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-Hans-CN,zh-CN;q=0.9,zh;q=0.8,en;q=0.7,en-GB;q=0.6,en-US;q=0.5,ja;q=0.4',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.53 Safari/537.36 Edg/80.0.361.33',
            'Connection' : 'keep-alive',
            'Cache-Control': 'no-cache',
            'Host': host,
            'Referer': ''
        }
cookies = None

def getValidSoupFromLink(link):
    r = requestSession.get(link, headers= headers, cookies=cookies, proxies=gProxies)
    if r.status_code != 200:
        logger.error("Fail to fetch content from [%s]" % link)
        return None
    soup = bs(r.text, 'html5lib')
    if soup == None:
        logger.error("Fail to parse content from [%s]" % link)
    return soup


def downloadImg(imgUrl, targetImgPath):
    logger.debug("Download: %s --> %s" % (imgUrl, targetImgPath))
    content = None
    try:
        retryCount = 4
        startUseProxyIdx = 2
        retryIdx = 0
        usedProxy = None
        while retryIdx < retryCount:
            retryIdx = retryIdx + 1
            time.sleep(random.random())
            if startUseProxyIdx >= 2:
                usedProxy = gProxies
            r = requestSession.get(imgUrl, headers = imgHeaders, verify = False, timeout=5, proxies=usedProxy)
            if r.status_code == 200:
                break
        if r.status_code != 200:
            logger.error("Fail to fetch image from [%s] to [%s], status_code = [%d]" % (imgUrl, targetImgPath, r.status_code))
        else:
            content = r.content
    except Exception as e:
        logger.error("Fail to download image from [%s] to [%s]: %s" % (imgUrl, targetImgPath, str(e)))
    if content == None:
        return False
    with open(targetImgPath, 'wb') as f:
        f.write(content)
    return True


def fetchImagesFromSubPage(subPageLink, chapterIdx, chapterDir):
    errorMsg = ''
    logger.debug("subPageLink: [%s], chapterId: [%d]" % (subPageLink, chapterIdx))
    url = subPageLink if subPageLink.find(site) == 0 else ( "https://" + subPageLink if subPageLink.find(host) == 0 else (site + subPageLink) )
    soup = getValidSoupFromLink(url)
    if soup == None:
        errorMsg = "Fail to get soup from url: [%s]" % subPageLink
        logger.error(errorMsg)
        return (False, errorMsg)
    #print(soup.prettify())
    contentDiv = soup.find('div', attrs = {'class': 'rd-article-wr clearfix'})
    if contentDiv == None:
        errorMsg = "Fail to get <div class='rd-article-wr clearfix'> from [%s]" % subPageLink
        logger.error(errorMsg)
        return (False, errorMsg)
    imgs = contentDiv.find_all('img')
    if len(imgs) == 0:
        errorMsg = "No <img> for chapter [%d] in <div class='rd-article-wr clearfix'> found [%s]" % (chapterIdx, subPageLink)
        logger.error(errorMsg)
        return (False, errorMsg)
    logger.info("[%d] <img> for chapter [%d] in <div class='rd-article-wr clearfix'> found [%s]" % (len(imgs), chapterIdx, subPageLink))
    '''
    vipImg = list(filter(lambda x:x['src'].find('vip.png') >=0, imgs))
    if len(vipImg) > 0:
        errorMsg = "This page [%d: %s] is for VIP, not fetch image" % (chapterIdx, subPageLink)
        logger.info(errorMsg)
        return (False, '')
    '''
    if not os.path.exists(chapterDir):
        os.mkdir(chapterDir)
    fileExistCount = len(os.listdir(chapterDir))
    if fileExistCount >= len(imgs):
        errorMsg = "[%d] images exist in [%s], more than image count from web [%d], no need download images" % (fileExistCount, chapterDir, len(imgs))
        logger.info(errorMsg)
        return (False, errorMsg)
    imgIdx = 0
    imageDledCount = 0
    for img in imgs:
        imgIdx = imgIdx + 1
        imgExt = img['data-original'].split('.')[-1]
        targetImgPath = chapterDir + ("%03d.%s" % (imgIdx, imgExt))
        ret = downloadImg(img['data-original'], targetImgPath)
        if ret:
            imageDledCount = imageDledCount + 1
    if imageDledCount != len(imgs):
        errorMsg = "Only [%d/%d] images downloaded successfully for [%s]" % (imageDledCount, len(imgs), subPageLink)
    return ((imageDledCount == len(imgs)), errorMsg)

def getComicNameFromSoup(soup):
    p = soup.find('p', attrs = {"class": "comic-title j-comic-title"})
    if p == None:
        logger.info("Fail to get <p> from soup")
        return ''
    return p.string

def login():
    global cookies
    loginPostData = {
        "name": "15194234617",
        "pass": '006akhm180',
        "islog": '1',
        "pcode": ""
    }
    loginUrl = "https://%s/index.php/api/user/login" % host
    r = requestSession.post(loginUrl, headers= headers, json=loginPostData)
    if r.status_code != 200:
        logger.error("Fail to login [%s]" % loginUrl)
        return False
    print(r.cookies)
    cookies = r.cookies
    return True

def getChapterLinks(mainPageSoup):
    aList = mainPageSoup.find_all('a', attrs = {'class': 'j-chapter-link'})
    finalChapterLink = ''
    maxChapterIdx = -1
    chapterLinks = {}
    for a in aList:
        chapterIdx = -1
        for content in a.contents:
            nums = re.findall('第(\d+)', str(content))
            if len(nums) > 0:
                chapterIdx = int(nums[0])
                if chapterIdx > maxChapterIdx:
                    maxChapterIdx = chapterIdx
            finalChapterKeys = re.findall('最終話', str(content))
            if len(finalChapterKeys) > 0:
                finalChapterLink = a['href']
        if chapterIdx == -1:
            logger.info("Fail to find the chapter number from <a> [%s]" % a.prettify())
            continue
        if chapterIdx not in chapterLinks.keys():
            chapterLinks[chapterIdx] = a['href']
    if finalChapterLink != '' and maxChapterIdx > 0:
        chapterLinks[maxChapterIdx + 1] = finalChapterLink
    return chapterLinks

def fetchComic(link, comicRootDir, comicInfo = {}):
    if len(comicInfo.keys()) == 0:
        comicInfo = {
                'name': '',
                'links': {
                    'twhm': '',
                    'yxhm': '',
                    '5wc': '',
                    'akhm': link
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

    subPages = getChapterLinks(soup)
    logger.info("Get total [%d] sub-pages" % len(subPages.keys()))
    for chapterIdx in sorted(subPages.keys()):
        if chapterIdx > lastChapterIdx:
            chapterDir = comicDir + ("%03d/" % chapterIdx)
            (ret, errorMsg) = fetchImagesFromSubPage(subPages[chapterIdx], chapterIdx, chapterDir)
            if ret:
                comicInfo['latestChapterIdx'] = chapterIdx
            else:
                if errorMsg != '':
                    jsonMsg = {
                        'subject': 'Caoliu topic: 爱看韩漫',
                        'channel': 'telegram',
                        'content': " - Fail to update chapter [%d] of [%s]. \n --- %s" % (chapterIdx, comicInfo['name'], errorMsg)
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
    if 'links' not in comicInfo.keys() or 'akhm' not in comicInfo['links'].keys():
        logger.info("No <links> or <links/akhm> in [%s] " % comicInfoFilePath)
        return None
    link = comicInfo['links']['akhm']
    if link == '':
        logger.info("No valid akhm link in [%s] " % comicInfoFilePath)
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

            if 'akhm' not in comicInfo['links'].keys():
                continue
            link = comicInfo['links']['akhm']
            latestChapterIdx = comicInfo['latestChapterIdx'] if 'latestChapterIdx' in comicInfo.keys() else 0
            name = comicInfo['name'] if 'name' in comicInfo.keys() else ''

            logger.info("----- Update Comic [%s] from chapter [%d], [%s] -----" % (name, latestChapterIdx, link))
            retData = fetchComic(link, targetDir, comicInfo)
            if retData['latestChapterIdx'] > latestChapterIdx:
                msg = "Comic [%s] is updated from [%d] to [%d]" % (retData['name'], latestChapterIdx, retData['latestChapterIdx'])
                logger.info(msg)
                notifMsg = notifMsg + msg + '\n'
                comicInfo['latestChapterIdx'] = retData['latestChapterIdx']
                configFileNeedUpdate = True
                with open(comicInfoFilePath, 'w') as f:
                    json.dump(retData, f, indent = 4, ensure_ascii = False)
            else:
                logger.info("No update for Comic [%s], still in [%d]" % (retData['name'], retData['latestChapterIdx']))
        if configFileNeedUpdate:
            jsonMsg = {
                'subject': 'Caoliu topic: 爱看韩漫',
                'channel': 'telegram',
                'content': " - " + notifMsg
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
    elif len(sys.argv) == 3:
        comicLink = sys.argv[-2]
        if sys.argv[-1] == 'new':
            logger.info("Try to insert new comic into disk from %s" % comicLink)
            soup = getValidSoupFromLink(comicLink)
            comicName = getComicNameFromSoup(soup)
            if comicName == '':
                print("No valid comic by [%s]" % comicLink)
                exit(1)
            comicDir = "%s/%s" % (targetDir, comicName)
            if os.path.exists(comicDir):
                print("[%s] by [%s] exists, no need manual update" % (comicName, comicLink))
                exit(0)
            else:
                os.mkdir(comicDir)
            comicInfo = {
                'name': comicName,
                'links': {
                    'twhm': '',
                    'yxhm': '',
                    '5wc': '',
                    'akhm': comicLink
                },
                'latestChapterIdx': 0
            }
            infoJsonPath = "%s/%s/info.json" % (targetDir, comicName)
            with open(infoJsonPath, 'w') as f:
                json.dump(comicInfo, f, indent = 4, ensure_ascii = False)
    elif len(sys.argv) == 4:
        chapterLink = sys.argv[-3]
        chapterIdx = int(sys.argv[-2])
        comicDir = sys.argv[-1]
        chapterDir = comicDir + ("%03d/" % chapterIdx)
        (ret, errorMsg) = fetchImagesFromSubPage(chapterLink, chapterIdx, chapterDir)
        if errorMsg != '':
            print(errorMsg)
    else:
        logger.error("Invalid parameter count")