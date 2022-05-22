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


def fetchImagesFromSubPage(subPageLink, chapterIdx, chapterDir):
    logger.debug("subPageLink: [%s], chapterId: [%d]" % (subPageLink, chapterIdx))
    url = subPageLink if subPageLink.find(site) == 0 else ( "https://" + subPageLink if subPageLink.find(host) == 0 else (site + subPageLink) )
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

    listUl = soup.find('ul', attrs = {'id': 'chapterlist'})
    if listUl == None:
        logger.error("Fail to get <ul id='chapterlist'> from [%s]" % link)
        return resultJson
    lis = listUl.find_all('li')
    if len(lis) == 0:
        logger.error("No <li> in <ul id='chapterlist'> found")
        return resultJson
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
                resultJson['latestChapterIdx'] = chapterIdx
            else:
                break
    return resultJson



if __name__ == "__main__":
    login()
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
                with open(configFilePath, 'w') as f:
                    json.dump(jsonConfig, f, indent = 4, ensure_ascii = False)
            else:
                logger.info("No update for Comic [%s], still in [%d]" % (comicConfigData['name'], comicConfigData['latestChapterIdx']))
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