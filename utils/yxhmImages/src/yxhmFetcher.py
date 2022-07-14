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
host = "yxhm.cc"
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
        r = imgSession.get(imgUrl)
        if r.status_code != 200:
            logger.error("Fail to fetch image from [%s]" % imgUrl)
        else:
            downloadSuccess = True
            f.write(r.content)
    return downloadSuccess

def generateUrl(subPagelink):
    if subPagelink.find("http://") == 0 or subPagelink.find("https://") == 0:
        return subPagelink
    if subPagelink.find(host) == 0 or subPagelink.find("www.yxhm99.com") == 0:
        return "https://" + subPagelink
    return site + subPagelink

def fetchImagesFromSubPage(subPageLink, chapterIdx, chapterDir):
    logger.debug("subPageLink: [%s], chapterId: [%d]" % (subPageLink, chapterIdx))
    url = generateUrl(subPageLink)
    soup = getValidSoupFromLink(url)
    if soup == None:
        return False
    #print(soup.prettify())
    contentDiv = soup.find('div', attrs = {'class': 'pictures9593'})
    if contentDiv == None:
        bookDiv = soup.find('div', attrs = {'class': 'bookinfo'})
        if bookDiv != None:
            logger.info("Page [%s] is for VIP, stop fetching" % subPageLink)
            return False
        logger.error("Fail to get <div class='pictures9593'> from [%s]" % subPageLink)
        return False
    imgs = contentDiv.find_all('img')
    if len(imgs) == 0:
        logger.error("No <img> for chapter [%d] in <div class='pictures9593'> found [%s]" % (subPageLink, chapterIdx))
        return False
    if not os.path.exists(chapterDir):
        os.mkdir(chapterDir)
    fileExistCount = len(os.listdir(chapterDir))
    if fileExistCount >= len(imgs):
        logger.info("[%d] images exist in [%s], more than image count from web [%d], no need download images" % (fileExistCount, chapterDir, len(imgs)))
        return True
    logger.info("[%d] <img> for chapter [%d] in <div class='pictures9593'> found [%s]" % (len(imgs), chapterIdx, subPageLink))
    imgIdx = 1
    for img in imgs:
        imgExt = img['src'].split('.')[-1]
        targetImgPath = chapterDir + ("%03d.%s" % (imgIdx, imgExt))
        ret = downloadImg(img['src'], targetImgPath)
        imgIdx = imgIdx + 1
    return True

def getComicNameFromSoup(soup):
    b = soup.find('b', attrs = {"class": "name"})
    if b == None:
        logger.info("Fail to get <b> from soup")
        return ''
    return b.string

def login():
    global cookies
    requestSession.post("https://yxhm.cc/member/index_do.php?fmdo=login&doPost=exit", headers=headers)
    loginPostData = {
        "fmdo": "login",
        "dopost": "login",
        "keeptime": str(3600 * 24),
        "gourl": "",
        "userid": "clinusalap",
        "pwd": "XkpBqVVJFUe7827"
    }
    loginUrl = "https://yxhm.cc/member/index_do.php?"
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

def fetchComic(link, comicRootDir, comicInfo = {}):
    if len(comicInfo.keys()) == 0:
        comicInfo = {
                'name': '',
                'links': {
                    'twhm': '',
                    'yxhm': link,
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

    listUl = soup.find('ul', attrs = {'id': 'chapterlist'})
    if listUl == None:
        logger.error("Fail to get <ul id='chapterlist'> from [%s]" % link)
        return comicInfo
    lis = listUl.find_all('li')
    if len(lis) == 0:
        logger.error("No <li> in <ul id='chapterlist'> found")
        return comicInfo
    subPages = {}
    for li in lis:
        a = li.find('a')
        if a == None:
            logger.info("No <a> under <li> [%s]" % li.prettify())
            continue
        em = li.find('em')
        if em == None:
            logger.info("No <em> under <li> [%s]" % li.prettify())
            continue
        if len(re.findall('\d+', em.string)) <= 0:
            continue
        chapterIdx = int(re.findall('\d+', em.string)[0])
        subPages[chapterIdx] = a['href']
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
    if 'links' not in comicInfo.keys() or 'yxhm' not in comicInfo['links'].keys():
        logger.info("No <links> or <links/yxhm> in [%s] " % comicInfoFilePath)
        return None
    link = comicInfo['links']['yxhm']
    if link == '':
        logger.info("No valid yxhm link in [%s] " % comicInfoFilePath)
        return None
    return comicInfo

if __name__ == "__main__":
    login()
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

            link = comicInfo['links']['yxhm']
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
                'subject': 'Caoliu topic: 优秀韩漫',
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
    else:
        logger.error("Invalid parameter count")