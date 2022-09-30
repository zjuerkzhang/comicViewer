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
logFilePath = ("%s/../log/%s.log" % (selfDir, fileName))
FORMAT = '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(filename = logFilePath, level = logging.INFO, format = FORMAT, datefmt = DATEFMT)

logger = logging.getLogger('BasicFetcher')
host = "twhm.net"
site = "https://" + host
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

def getValidSoupFromLink(link):
    r = requestSession.get(link, headers= headers, cookies=cookies)
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
        try:
            r = imgSession.get(imgUrl)
            if r.status_code != 200:
                logger.error("Fail to fetch image from [%s]" % imgUrl)
            else:
                downloadSuccess = True
                f.write(r.content)
        except:
            logger.error("Fail to download image from [%s] to [%s]" % (imgUrl, targetImgPath))
    return downloadSuccess


def fetchImagesFromSubPage(subPageLink, chapterIdx, chapterDir):
    logger.debug("subPageLink: [%s], chapterId: [%d]" % (subPageLink, chapterIdx))
    url = subPageLink if subPageLink.find(site) == 0 else ( "https://" + subPageLink if subPageLink.find(host) == 0 else (site + subPageLink) )
    soup = getValidSoupFromLink(url)
    if soup == None:
        return False
    #print(soup.prettify())
    contentDiv = soup.find('div', attrs = {'style': 'max-width:720px;margin:0 auto;text:center;'})
    if contentDiv == None:
        logger.error("Fail to get <div style='max-width:720px;margin:0 auto;text:center;'> from [%s]" % subPageLink)
        return False
    imgs = contentDiv.find_all('img')
    if len(imgs) == 0:
        logger.error("No <img> for chapter [%d] in <div class='pictures9593'> found [%s]" % (subPageLink, chapterIdx))
        return False
    logger.info("[%d] <img> for chapter [%d] in <div class='pictures9593'> found [%s]" % (len(imgs), chapterIdx, subPageLink))
    vipImg = list(filter(lambda x:x['src'].find('vip.png') >=0, imgs))
    if len(vipImg) > 0:
        logger.info("This page [%d: %s] is for VIP, not fetch image" % (chapterIdx, subPageLink))
        return False
    if not os.path.exists(chapterDir):
        os.mkdir(chapterDir)
    fileExistCount = len(os.listdir(chapterDir))
    if fileExistCount >= len(imgs):
        logger.info("[%d] images exist in [%s], more than image count from web [%d], no need download images" % (fileExistCount, chapterDir, len(imgs)))
        return True
    imgIdx = 0
    failCount = 0
    for img in imgs:
        imgIdx = imgIdx + 1
        imgExt = img['src'].split('.')[-1]
        targetImgPath = chapterDir + ("%03d.%s" % (imgIdx, imgExt))
        ret = downloadImg(img['src'], targetImgPath)
        if not ret:
            logger.info("Fail to download image from [%s] to [%s]" % (img['src'], targetImgPath))
            failCount = failCount + 1
    if failCount >= int(imgIdx/10):
        logger.info("Fail to download [%d/%d] images from [%s]" % (failCount, imgIdx, img['src']))
        return False
    return True

def getComicNameFromSoup(soup):
    h1 = soup.find('h1', attrs = {"class": "fed-part-eone fed-font-xvi"})
    if h1 == None:
        logger.info("Fail to get <h1> from soup")
        return ''
    a = h1.find('a')
    if a == None:
        logger.info("Fail to get <a> under <h1>")
        return ''
    return a.string

def login():
    global cookies
    requestSession.post("https://www.twhm.net/member/index_do.php?fmdo=login&dopost=exit", headers=headers)
    loginPostData = {
        "action": "login",
        "keeptime": str(3600 * 24),
        "gourl": "https://www.twhm.net/",
        "user_name": "cruslefrat",
        "user_pwd": "9gU9CNBhMWH7Azd"
    }
    loginUrl = "https://www.twhm.net/member/ajax_login.php?"
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

def getChapterLinks(mainPageSoup):
    aList = mainPageSoup.find_all('a', attrs = {'class': 'fed-btns-info fed-rims-info fed-part-eone'})
    chapterLinks = {}
    for a in aList:
        chapterIdx = -1
        for content in a.contents:
            nums = re.findall('第(\d+)', content)
            if len(nums) > 0:
                chapterIdx = int(nums[0])
        if chapterIdx == -1:
            logger.info("Fail to find the chapter number from <a> [%s]" % a.prettify())
            continue
        if chapterIdx not in chapterLinks.keys():
            chapterLinks[chapterIdx] = a['href']
    return chapterLinks

def fetchComic(link, comicRootDir, comicInfo = {}):
    if len(comicInfo.keys()) == 0:
        comicInfo = {
                'name': '',
                'links': {
                    'twhm': link,
                    'yxhm': '',
                    '5wc': ''
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
            ret = fetchImagesFromSubPage(subPages[chapterIdx], chapterIdx, chapterDir)
            if ret:
                comicInfo['latestChapterIdx'] = chapterIdx
            else:
                break
    return comicInfo

def fetchComicChapter(link, comicRootDir, chapterIndex):
    soup = getValidSoupFromLink(link)
    comicName = getComicNameFromSoup(soup)
    comicDir = comicRootDir + '/' + comicName + '/'
    if not os.path.exists(comicDir):
        os.mkdir(comicDir)
    subPages = getChapterLinks(soup)
    if chapterIndex in subPages.keys():
        chapterDir = comicDir + ("%03d/" % chapterIndex)
        ret = fetchImagesFromSubPage(subPages[chapterIndex], chapterIndex, chapterDir)
        if not ret:
            print("Fail to fetch images for chapter [%d] from page [%s]" % (chapterIndex, subPages[chapterIndex]))
    else:
        print("No chapter [%d] in page [%s]" % (chapterIndex, link))

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
    if 'links' not in comicInfo.keys() or 'twhm' not in comicInfo['links'].keys():
        logger.info("No <links> or <links/twhm> in [%s] " % comicInfoFilePath)
        return None
    link = comicInfo['links']['twhm']
    if link == '':
        logger.info("No valid twhm link in [%s] " % comicInfoFilePath)
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

            link = comicInfo['links']['twhm']
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
                'subject': 'Caoliu topic: 图文韩漫',
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
        chapterIdx = int(sys.argv[-1])
        fetchComicChapter(comicLink, chapterIdx)
    else:
        logger.error("Invalid parameter count")