from BaseFetcher import BaseFetcher
import time
import random
import json
import json
from base64 import b64decode
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
import hashlib
from PIL import Image
from io import BytesIO
import math
import re

class WuwuhanmanFetcher(BaseFetcher):
    def __init__(self, comicRootPath, webSiteName):
        super().__init__(comicRootPath, webSiteName)
        self.proxy = {
            'http': 'http://192.168.119.47:8080',
            'https': 'http://192.168.119.47:8080'
        }

    def parseComicWebToGetComicName(self, soup):
        div = soup.find('div', attrs = {"class": "detail-tit"})
        if div == None:
            self.logger.info("Fail to get <div class='detail-tit'> from soup [%s]" % self.comicLink)
            return ''
        h1 = div.find('h1')
        if h1 == None:
            self.logger.info("Fail to get <div class='detail-tit'><h1> from soup [%s]" % self.comicLink)
            return ''
        return h1.string

    def parseComicWebToGetChapterLinks(self, soup):
        spans = soup.find_all('span', attrs = {'class': 'itemcata-title'})
        aList = list(map(lambda x:x.parent, spans))
        finalChapterLink = ''
        maxChapterIdx = -1
        chapterLinks = {}
        for a in aList:
            chapterIdx = -1
            nums = re.findall(self.getSearchRegexPattern(), str(a['title']))
            if len(nums) > 0:
                chapterIdx = int(nums[0])
                if chapterIdx > maxChapterIdx:
                    maxChapterIdx = chapterIdx
            else:
                finalChapterFound = len(re.findall('最終話', str(a['title']))) > 0 or len(re.findall('最终话', str(a['title']))) > 0
                if finalChapterFound:
                    finalChapterLink = a['href']
            if chapterIdx == -1:
                self.logger.info("Fail to find the chapter number from <a> [%s]" % a.prettify())
                continue
            if chapterIdx not in chapterLinks.keys():
                chapterLinks[chapterIdx] = a['href']
        if finalChapterLink != '' and maxChapterIdx > 0:
            chapterLinks[maxChapterIdx + 1] = finalChapterLink


        host = self.comicLink.split('/')[2]
        site = "https://" + host
        for key in chapterLinks.keys():
            chapterLinks[key] = self.regulateSublink(chapterLinks[key], host, site)
        return chapterLinks

    def parseChapterWebToGetImageLinks(self, soup):
        divs = soup.find_all('div', attrs = {'class': 'cropped'})
        if len(divs) == 0:
            self.logger.info("Fail to get <div class='cropped'> from soup")
            return []
        imgLinks = list(map(lambda x: x['data-src'], divs))
        return imgLinks

    def downloadSubBinaryFile(self, binUrl, parentUrl):
        content = None
        try:
            retryCount = 4
            startUseProxyIdx = 2
            retryIdx = 0
            usedProxy = self.proxy
            while retryIdx < retryCount:
                retryIdx = retryIdx + 1
                time.sleep(random.random())
                if startUseProxyIdx >= 2:
                    usedProxy = self.proxy
                imgHeaders = json.loads(self.baseHttpHeadersStr)
                imgHeaders['Host'] = binUrl.split('/')[2]
                imgHeaders['Referer'] = parentUrl
                r = self.httpClient.get(binUrl, headers = imgHeaders, verify = False, timeout=10, proxies=usedProxy)
                if r.status_code == 200:
                    break
            if r.status_code != 200:
                self.logger.error("Fail to fetch image from [%s] , status_code = [%d]" % (binUrl.strip(), r.status_code))
            else:
                content = r.content
        except Exception as e:
            self.logger.error("Fail to download image from [%s]: %s" % (binUrl.strip(), str(e)))
        #print(type(content))
        decryptedContent = None
        try:
            key = b'aaaaaaaaaaaaaaaa'
            iv = b'0123456789aaaaaa'
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decryptedContent = unpad(cipher.decrypt(content), AES.block_size)
        except Exception as e:
            self.logger.error("Fail to decrypt content from  [%s]: %s" % (binUrl.strip(), str(e)))
        return decryptedContent

    def generateTwoBinUrls(self, imgUrl):
        ss = imgUrl.split('.')
        urlWithoutExt = '.'.join(ss[:-1])
        return [
            urlWithoutExt + '.b_0',
            urlWithoutExt + '.b_1'
        ]

    def getCorpCount(self, bookId, pageNum):
        s = "%s%s" % (bookId, pageNum)
        b = bytes(s, encoding = 'utf-8')
        hashcode = bytes(hashlib.md5(b).hexdigest(), encoding = 'utf-8')
        key = hashcode[-1] % 10
        if key == 0:
            return 44;
        elif key == 1:
            return 48;
        elif key == 2:
            return 52;
        elif key == 3:
            return 56;
        elif key == 4:
            return 60;
        elif key == 5:
            return 64;
        elif key == 6:
            return 68;
        elif key == 7:
            return 72;
        elif key == 8:
            return 76;
        elif key == 9:
            return 80
        else:
            return 10

    def regularateImageAndSave(self, imgBytes, corpCount, targetImgPath):
        im = None
        try:
            im = Image.open(BytesIO(imgBytes))
        except Exception as e:
            self.logger("Fail to open image from binary for [%s]: %s" % (targetImgPath, str(e)))
            return False
        size = im.size
        newIm = Image.new(im.mode, (size[0], size[1]))
        unitHeight = math.floor(size[1] / corpCount)
        heightMod = (size[1] % corpCount)
        i = 0
        while i < corpCount:
            if i == 0:
                sourceH = unitHeight + heightMod
                targetY = 0
            else:
                sourceH = unitHeight
                targetY = unitHeight * i + heightMod
            sourceY = size[1] - unitHeight * (i+1) - heightMod

            sourceBox = (0, sourceY, size[0], sourceY + sourceH)
            corp = im.crop(sourceBox)
            newIm.paste(corp, (0, targetY))
            i = i + 1
        newIm.save(targetImgPath)
        return True

    def downloadImg(self, imgUrl, targetImgPath, parentUrl):
        self.logger.debug("Download: %s --> %s" % (imgUrl, targetImgPath))
        urls = self.generateTwoBinUrls(imgUrl)
        content = None
        for url in urls:
            c = self.downloadSubBinaryFile(url, parentUrl)
            if c == None:
                self.logger.error("Fail to fetch image from [%s] to [%s]" % (imgUrl.strip(), targetImgPath.strip()))
                return False
            if content == None:
                content = c
            else:
                content = content + c
        ba = bytearray(content)
        if ba[0] != 0 or ba[1] != 0:
            self.logger.error("First byte of binary from [%s] is wrong, fail to download [%s]" % (imgUrl.strip(), targetImgPath.strip()))
            return False
        bookId = ba[2] * 256 + ba[3]
        pageNumber = ba[4] *16777216 + ba[5] * 65536 + ba[6] * 256 + ba[7]
        #print("bookId: %d, pageNumer: %d" % (bookId, pageNumber))
        corpCount = self.getCorpCount(bookId, pageNumber)
        #print(corpCount)
        # fill magic number for jpg
        ba[0] = 0xff
        ba[1] = 0xd8
        ba[2] = 0xff
        ba[3] = 0xe0
        ba[4] = 0x00
        ba[5] = 0x10
        ba[6] = 0x4a
        ba[7] = 0x46
        ba[8] = 0x49
        ba[9] = 0x46
        ba[10] = 0x00
        ba[11] = 0x01

        #with open(targetImgPath, 'wb') as f:
        #    f.write(ba)
        return self.regularateImageAndSave(ba, corpCount, targetImgPath)

if __name__ == '__main__':
    a = WuwuhanmanFetcher('', '')
    a.setInternalParameters('https://www.55comic.com/book/4966', '繼母與繼姐', 119)
    a.fetchImagesFromChapterPage('https://www.55comic.com/free-chapter/42781?t=20260415', 117, "/home/kzhang/github/comicViewer/comic/00-连载中/繼母與繼姐/117/")
    #a.setInternalParameters('https://www.55comic.com/free-chapter/42781?t=20260415')
    #a.downloadImg('https://bmigmij-wuwu.sqxxov.com/break_2/static/upload/book/4966/42781/3078938.jpg', 'a.jpg', '')
