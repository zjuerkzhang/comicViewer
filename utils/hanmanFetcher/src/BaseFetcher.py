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

class BaseFetcher(object):
    @classmethod
    def class_name(cls):
        return cls.__name__


    def __init__(self, comicRootPath, webSiteName) -> None:
        selfDir = os.path.dirname(os.path.abspath(__file__))
        logFilePath = ("%s/../log/log.log" % (selfDir))
        FORMAT = '%(asctime)s %(name)s [%(levelname)s]: %(message)s'
        DATEFMT = '%Y-%m-%d %H:%M:%S'
        logging.basicConfig(filename = logFilePath, level = logging.INFO, format = FORMAT, datefmt = DATEFMT)
        self.logger = logging.getLogger(self.class_name())
        self.comicRootPath = comicRootPath
        self.webSiteName = webSiteName
        self.proxy = None



    def getSearchRegexPattern(self):
        return f"{self.prefix}\s*第(\d+)"
        if self.prefix == '':
            return '\s*^第(\d+)'
        else:
            return '^%s\s*第(\d+)' % self.prefix


    def setInternalParameters(self, link = '', name = '', lastChapterIdx = 0, prefix = ''):
        baseHeaders = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,en-US;q=0.7,en;q=0.3',
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Connection' : 'keep-alive',
            'Cache-Control': 'no-cache'
        }
        self.baseHttpHeadersStr = json.dumps(baseHeaders)
        self.httpClient = requests.Session()

        self.comicLink = link
        if name == '':
            self.comicName = self.getComicNameFromMainLink()
        else:
            self.comicName = name

        if self.comicName != '' and self.comicName != None:
            self.comicDirPath = '%s/%s/' % (self.comicRootPath, self.comicName)
        else:
            self.comicDirPath = ''
        self.prefix = prefix

        self.lastChapterIdx = lastChapterIdx
        self.LatestChapterIdx = lastChapterIdx
        ret = self.login()
        if ret == False:
            self.logger.error("Login into [%s] site failed" % self.webSiteName)
        return ret


    def login(self):
        return True


    def regulateSublink(self, srcLink, host, site):
        return srcLink if srcLink.find(site) == 0 else ( "https://" + srcLink if srcLink.find(host) == 0 else (site + srcLink) )


    def getValidSoupFromLink(self, link):
        headers = json.loads(self.baseHttpHeadersStr)
        headers['Host'] = link.split('/')[2]
        try:
            r = self.httpClient.get(link, headers= headers, timeout=10, proxies= self.proxy)
        except:
            self.logger.error("Exception occurs when fetching content from [%s]" % link)
            return None
        if r.status_code != 200:
            self.logger.error("Fail to fetch content from [%s]" % link)
            return None
        soup = bs(r.text, 'html5lib')
        if soup == None:
            self.logger.error("Fail to parse content from [%s]" % link)
        return soup


    def getComicNameFromMainLink(self):
        soup = self.getValidSoupFromLink(self.comicLink)
        if soup == None:
            self.logger.error("Fail to get soup from comic web [%s]" % self.comicLink)
            return ''
        return self.parseComicWebToGetComicName(soup)

    def parseComicWebToGetComicName(self, soup):
        return ''


    def getChapterLinks(self):
        soup = self.getValidSoupFromLink(self.comicLink)
        if soup == None:
            self.logger.error("Fail to get soup from comic web [%s]" % self.comicLink)
            return None
        chapterLinks = self.parseComicWebToGetChapterLinks(soup)
        if chapterLinks == None or len(chapterLinks.keys()) == 0:
            self.logger.error("No valid chapter links from comic web [%s]" % self.comicLink)
        return chapterLinks


    def parseComicWebToGetChapterLinks(self, soup):
        return None


    def getImageLinksFromChapterPage(self, chapterLink):
        soup = self.getValidSoupFromLink(chapterLink)
        if soup == None:
            self.logger.error("Fail to get soup from chapter web [%s]" % chapterLink)
            return []
        imgLinks = self.parseChapterWebToGetImageLinks(soup)
        if len(imgLinks) == 0:
            self.logger.error("No valid image links from chapter web [%s]" % chapterLink)
        return imgLinks


    def parseChapterWebToGetImageLinks(self, soup):
        return []


    def downloadImg(self, imgUrl, targetImgPath, parentUrl):
        self.logger.debug("Download: %s --> %s" % (imgUrl, targetImgPath))
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
                    usedProxy = self.proxy
                imgHeaders = json.loads(self.baseHttpHeadersStr)
                imgHeaders['Host'] = imgUrl.split('/')[2]
                imgHeaders['Referer'] = parentUrl
                r = self.httpClient.get(imgUrl, headers = imgHeaders, verify = False, timeout=10, proxies=usedProxy)
                if r.status_code == 200:
                    break
            if r.status_code != 200:
                self.logger.error("Fail to fetch image from [%s] to [%s], status_code = [%d]" % (imgUrl.strip(), targetImgPath.strip(), r.status_code))
                self.logger.info("Try to download image by command: [curl -f -o %s %s]" % (targetImgPath.strip(), imgUrl.strip()))
            else:
                content = r.content
        except Exception as e:
            self.logger.error("Fail to download image from [%s] to [%s]: %s" % (imgUrl.strip(), targetImgPath.strip(), str(e)))
            self.logger.info("Try to download image by command: [curl -f -o %s %s]" % (targetImgPath.strip(), imgUrl.strip()))
        if content == None:
            return False
        with open(targetImgPath, 'wb') as f:
            f.write(content)
        return True


    def fetchImagesFromChapterPage(self, chapterLink, chapterIdx, chapterDirPath):
        errorMsg = ''
        imgLinks = self.getImageLinksFromChapterPage(chapterLink)
        self.logger.info("[%d] <img>s found in chapter [%s|%d|%s]" % (len(imgLinks), self.comicName, chapterIdx, chapterLink))
        if len(imgLinks) == 0:
            errorMsg = "No <img> found in chapter [%s|%d|%s]" % (self.comicName, chapterIdx, chapterLink)
            return (False, errorMsg)
        if not os.path.exists(chapterDirPath):
            os.mkdir(chapterDirPath)
        fileExistCount = len(os.listdir(chapterDirPath))
        if fileExistCount >= len(imgLinks):
            errorMsg = "[%d] images exist in disk, more than [%d] from web [%s|%d|%s]" % (fileExistCount, len(imgLinks), self.comicName, chapterIdx, chapterLink)
            self.logger.info(errorMsg)
            return (False, errorMsg)
        imgIdx = 0
        imageDledCount = 0
        for imgLink in imgLinks:
            imgIdx = imgIdx + 1
            imgExt = imgLink.split('.')[-1]
            targetImgPath = chapterDirPath + ("%03d.%s" % (imgIdx, imgExt))
            ret = self.downloadImg(imgLink, targetImgPath, chapterLink)
            if ret:
                imageDledCount = imageDledCount + 1
        if imageDledCount != len(imgLinks):
            errorMsg = "Only [%d/%d] images downloaded successfully from [%s|%d|%s]" % (imageDledCount, len(imgLinks), self.comicName, chapterIdx, chapterLink)
        return ((imageDledCount >= len(imgLinks) - 1), errorMsg)


    def fetchComic(self):
        if self.comicDirPath == '':
            self.logger.error('No valid comicName for [%s]' % self.comicLink)
            return

        if not os.path.exists(self.comicDirPath):
            os.mkdir(self.comicDirPath)

        subPageLinks  = self.getChapterLinks()
        subLinkCount = 0 if subPageLinks == None else len(subPageLinks.keys())
        self.logger.info("Get total [%d] chapter pages for [%s|%s]" % (subLinkCount, self.comicName, self.comicLink))
        if subPageLinks == None or len(subPageLinks.keys()) == 0:
            return

        errorMsg = ''
        for chapterIdx in sorted(subPageLinks.keys()):
            if chapterIdx > self.lastChapterIdx:
                chapterDir = self.comicDirPath + ("%03d/" % chapterIdx)
                (ret, errorMsg) = self.fetchImagesFromChapterPage(subPageLinks[chapterIdx], chapterIdx, chapterDir)
                if ret:
                    self.LatestChapterIdx = chapterIdx
                else:
                    break
        self.notifyComicFetchResult(errorMsg)


    def getLatestChapterIdx(self):
        return self.LatestChapterIdx


    def getComicName(self):
        return self.comicName


    def notifyComicFetchResult(self, errorMsg):
        needNotify = False
        notificationUrl="http://127.0.0.1:59999/notify"
        msg = 'Summary for task of [%s]:' % self.comicName
        if self.LatestChapterIdx > self.lastChapterIdx:
            msg = msg + ('\n -- updated from chapter [%d] to [%d]' % (self.lastChapterIdx, self.LatestChapterIdx))
            needNotify = True
        if errorMsg != '':
            msg = msg + '\n -- <Error>: ' + errorMsg
            needNotify = True
        if needNotify:
            jsonMsg = {
                        'subject': 'Caoliu topic: %s' % self.webSiteName,
                        'channel': 'telegram',
                        'content': msg
                    }
            requests.post(notificationUrl, json = jsonMsg)
