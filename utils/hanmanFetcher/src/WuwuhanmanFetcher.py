# -*- coding: utf-8 -*-

from BaseFetcher import BaseFetcher

import time
import random
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

        # 新版 BMI 图片：
        # imgUrl -> data-bmi-manifest
        #
        # 这样可以保持 BaseFetcher 原来的接口不变。
        self.bmiManifests = {}

    def parseComicWebToGetComicName(self, soup):
        div = soup.find('div', attrs={"class": "detail-tit"})

        if div is None:
            self.logger.info(
                "Fail to get <div class='detail-tit'> from soup [%s]"
                % self.comicLink
            )
            return ''

        h1 = div.find('h1')

        if h1 is None:
            self.logger.info(
                "Fail to get <div class='detail-tit'><h1> from soup [%s]"
                % self.comicLink
            )
            return ''

        return h1.string

    def parseComicWebToGetChapterLinks(self, soup):
        aList = soup.find_all(
            'a',
            attrs={'class': 'sp-chapter-item'}
        )

        finalChapterLink = ''
        maxChapterIdx = -1
        chapterLinks = {}

        for a in aList:
            chapterIdx = -1

            nums = re.findall(
                self.getSearchRegexPattern(),
                str(a['title'])
            )

            if len(nums) > 0:
                chapterIdx = int(nums[0])

                if chapterIdx > maxChapterIdx:
                    maxChapterIdx = chapterIdx

            else:
                finalChapterFound = (
                    len(re.findall('最終話', str(a['title']))) > 0
                    or
                    len(re.findall('最终话', str(a['title']))) > 0
                )

                if finalChapterFound:
                    finalChapterLink = a['href']

            if chapterIdx == -1:
                self.logger.info(
                    "Fail to find the chapter number from <a> [%s]"
                    % a.prettify()
                )
                continue

            if chapterIdx not in chapterLinks:
                chapterLinks[chapterIdx] = a['href']

        if finalChapterLink != '' and maxChapterIdx > 0:
            chapterLinks[maxChapterIdx + 1] = finalChapterLink

        host = self.comicLink.split('/')[2]
        site = "https://" + host

        for key in chapterLinks.keys():
            chapterLinks[key] = self.regulateSublink(
                chapterLinks[key],
                host,
                site
            )

        return chapterLinks

    # ------------------------------------------------------------------
    # 新版：
    # 解析 data-bmi-manifest，同时保持原来的返回值仍然是 imgUrl
    # ------------------------------------------------------------------
    def parseChapterWebToGetImageLinks(self, soup):

        divs = soup.find_all(
            'div',
            attrs={'class': 'cropped'}
        )

        if len(divs) == 0:
            self.logger.info(
                "Fail to get <div class='cropped'> from soup"
            )
            return []

        # 每次解析章节时重新建立
        self.bmiManifests = {}

        imgLinks = []

        for div in divs:

            imgUrl = div.get('data-src')
            manifest = div.get('data-bmi-manifest')

            if not imgUrl:
                self.logger.warning(
                    "Image div has no data-src: %s",
                    str(div)[:300]
                )
                continue

            imgLinks.append(imgUrl)

            if manifest:
                self.bmiManifests[imgUrl] = manifest

                self.logger.debug(
                    "BMI manifest found: %s",
                    imgUrl
                )

            else:
                self.logger.warning(
                    "No data-bmi-manifest for image [%s]",
                    imgUrl
                )

        return imgLinks

    # ------------------------------------------------------------------
    # Base64URL -> JSON
    # ------------------------------------------------------------------
    def decodeBmiManifest(self, manifest):

        try:
            # manifest 是 Base64URL 编码
            s = manifest.replace('-', '+').replace('_', '/')

            # 补齐 Base64 padding
            s += '=' * (-len(s) % 4)

            data = b64decode(s)

            result = json.loads(
                data.decode('utf-8')
            )

            return result

        except Exception as e:
            self.logger.error(
                "Fail to decode BMI manifest: %s",
                str(e)
            )
            return None

    # ------------------------------------------------------------------
    # 从 BMI manifest 中获取 JPEG page chunks
    # ------------------------------------------------------------------
    def getManifestChunkUrls(self, manifest):

        data = self.decodeBmiManifest(manifest)

        if data is None:
            return []

        try:

            variants = data.get('variants', {})

            # 当前页面同时可能存在 avif / jpeg
            jpeg = variants.get('jpeg')

            if jpeg is None:
                self.logger.error(
                    "JPEG variant not found in BMI manifest"
                )
                return []

            renditions = jpeg.get('renditions', [])

            rendering = None

            # 找真正的 page rendering
            for r in renditions:
                if r.get('role') == 'page':
                    rendering = r
                    break

            # 如果没有 role=page，退一步使用第一个 rendering
            if rendering is None and len(renditions) > 0:
                rendering = renditions[0]

            if rendering is None:
                self.logger.error(
                    "JPEG rendering not found in BMI manifest"
                )
                return []

            chunks = rendering.get('chunks', [])

            if len(chunks) == 0:
                self.logger.error(
                    "No chunks found in BMI manifest"
                )
                return []

            # 按 index 排序
            chunks = sorted(
                chunks,
                key=lambda x: x.get('index', 0)
            )

            urls = []

            for chunk in chunks:
                url = chunk.get('url')

                if url:
                    urls.append(url)

            return urls

        except Exception as e:
            self.logger.error(
                "Fail to parse BMI manifest: %s",
                str(e)
            )
            return []

    # ------------------------------------------------------------------
    # 下载一个 chunk
    #
    # 注意：
    # 这里已经不能 AES 解密！
    #
    # 新版流程：
    #
    #   page/0
    #   page/1
    #      ↓
    #   拼接
    #      ↓
    #   AES-CBC 解密
    #
    # ------------------------------------------------------------------
    def downloadBinaryFile(self, binUrl, parentUrl):

        content = None

        try:

            retryCount = 4

            for retryIdx in range(retryCount):

                time.sleep(random.random())

                imgHeaders = json.loads(
                    self.baseHttpHeadersStr
                )

                # 对 Google Storage 请求
                imgHeaders['Host'] = binUrl.split('/')[2]

                imgHeaders['Referer'] = parentUrl

                # 浏览器实际请求中有 Origin。
                # requests 本身不需要 CORS，但加上更接近浏览器请求。
                imgHeaders['Origin'] = 'https://www.55comic.com'

                r = self.httpClient.get(
                    binUrl,
                    headers=imgHeaders,
                    verify=False,
                    timeout=10,
                    proxies=self.proxy
                )

                if r.status_code == 200:
                    content = r.content
                    break

                self.logger.warning(
                    "Fail to fetch chunk [%s], status=%d, retry=%d/%d",
                    binUrl,
                    r.status_code,
                    retryIdx + 1,
                    retryCount
                )

            if content is None:
                self.logger.error(
                    "Fail to fetch chunk [%s]",
                    binUrl
                )

        except Exception as e:

            self.logger.error(
                "Fail to download chunk from [%s]: %s",
                binUrl,
                str(e)
            )

        return content

    # ------------------------------------------------------------------
    # AES-CBC 解密
    #
    # 注意：必须对“合并后的完整 ciphertext”进行解密。
    # ------------------------------------------------------------------
    def decryptContent(self, content):

        if content is None:
            return None

        try:

            key = b'aaaaaaaaaaaaaaaa'
            iv = b'0123456789aaaaaa'

            cipher = AES.new(
                key,
                AES.MODE_CBC,
                iv
            )

            decryptedContent = unpad(
                cipher.decrypt(content),
                AES.block_size
            )

            return decryptedContent

        except Exception as e:

            self.logger.error(
                "Fail to decrypt content: %s",
                str(e)
            )

            return None

    # ------------------------------------------------------------------
    # 旧版 .b_0 / .b_1 URL
    #
    # 保留这个函数，以便以后网站回退旧协议时使用。
    # ------------------------------------------------------------------
    def generateTwoBinUrls(self, imgUrl):

        ss = imgUrl.split('.')

        urlWithoutExt = '.'.join(ss[:-1])

        return [
            urlWithoutExt + '.b_0',
            urlWithoutExt + '.b_1'
        ]

    # ------------------------------------------------------------------
    # 根据 bookId + pageNumber 计算切片数量
    # ------------------------------------------------------------------
    def getCorpCount(self, bookId, pageNum):

        s = "%s%s" % (bookId, pageNum)

        b = bytes(
            s,
            encoding='utf-8'
        )

        hashcode = bytes(
            hashlib.md5(b).hexdigest(),
            encoding='utf-8'
        )

        key = hashcode[-1] % 10

        if key == 0:
            return 44
        elif key == 1:
            return 48
        elif key == 2:
            return 52
        elif key == 3:
            return 56
        elif key == 4:
            return 60
        elif key == 5:
            return 64
        elif key == 6:
            return 68
        elif key == 7:
            return 72
        elif key == 8:
            return 76
        elif key == 9:
            return 80
        else:
            return 10

    # ------------------------------------------------------------------
    # 重新排列图片切片
    # ------------------------------------------------------------------
    def regularateImageAndSave(
        self,
        imgBytes,
        corpCount,
        targetImgPath
    ):

        im = None

        try:

            im = Image.open(
                BytesIO(imgBytes)
            )

        except Exception as e:

            self.logger.error(
                "Fail to open image from binary for [%s]: %s",
                targetImgPath,
                str(e)
            )

            return False

        size = im.size

        newIm = Image.new(
            im.mode,
            (size[0], size[1])
        )

        unitHeight = math.floor(
            size[1] / corpCount
        )

        heightMod = size[1] % corpCount

        i = 0

        while i < corpCount:

            if i == 0:

                sourceH = unitHeight + heightMod
                targetY = 0

            else:

                sourceH = unitHeight
                targetY = (
                    unitHeight * i +
                    heightMod
                )

            sourceY = (
                size[1]
                - unitHeight * (i + 1)
                - heightMod
            )

            sourceBox = (
                0,
                sourceY,
                size[0],
                sourceY + sourceH
            )

            corp = im.crop(sourceBox)

            newIm.paste(
                corp,
                (0, targetY)
            )

            i = i + 1

        newIm.save(targetImgPath)

        return True

    # ------------------------------------------------------------------
    # 新版 downloadImg
    # ------------------------------------------------------------------
    def downloadImg(
        self,
        imgUrl,
        targetImgPath,
        parentUrl
    ):

        self.logger.debug(
            "Download: %s --> %s",
            imgUrl,
            targetImgPath
        )

        # --------------------------------------------------------------
        # 1. 找 manifest
        # --------------------------------------------------------------
        manifest = self.bmiManifests.get(imgUrl)

        if manifest:

            self.logger.debug(
                "Using BMI manifest for [%s]",
                imgUrl
            )

            # ----------------------------------------------------------
            # 2. 从 manifest 得到 page/0, page/1
            # ----------------------------------------------------------
            urls = self.getManifestChunkUrls(
                manifest
            )

            if len(urls) == 0:

                self.logger.error(
                    "No BMI chunks found for [%s]",
                    imgUrl
                )

                return False

            # ----------------------------------------------------------
            # 3. 下载所有 chunk
            #
            # 千万不要在这里解密
            # ----------------------------------------------------------
            chunks = []

            for url in urls:

                self.logger.debug(
                    "Download BMI chunk: %s",
                    url
                )

                c = self.downloadBinaryFile(
                    url,
                    parentUrl
                )

                if c is None:

                    self.logger.error(
                        "Fail to fetch BMI chunk [%s] for [%s]",
                        url,
                        imgUrl
                    )

                    return False

                chunks.append(c)

            # ----------------------------------------------------------
            # 4. 先合并 ciphertext
            # ----------------------------------------------------------
            encryptedContent = b''.join(
                chunks
            )

            self.logger.debug(
                "BMI encrypted size: %d",
                len(encryptedContent)
            )

            # ----------------------------------------------------------
            # 5. 对完整 ciphertext AES-CBC 解密
            # ----------------------------------------------------------
            content = self.decryptContent(
                encryptedContent
            )

            if content is None:

                self.logger.error(
                    "Fail to decrypt BMI image [%s]",
                    imgUrl
                )

                return False

        else:

            # ----------------------------------------------------------
            # 没有 manifest：
            # 尝试兼容旧版 .b_0 / .b_1
            # ----------------------------------------------------------
            self.logger.warning(
                "No BMI manifest for [%s], "
                "try legacy .b_0/.b_1 mode",
                imgUrl
            )

            urls = self.generateTwoBinUrls(
                imgUrl
            )

            chunks = []

            for url in urls:

                c = self.downloadBinaryFile(
                    url,
                    parentUrl
                )

                if c is None:

                    self.logger.error(
                        "Fail to fetch legacy chunk [%s]",
                        url
                    )

                    return False

                # 旧版每个 chunk 是单独 AES 加密的
                c = self.decryptContent(c)

                if c is None:

                    self.logger.error(
                        "Fail to decrypt legacy chunk [%s]",
                        url
                    )

                    return False

                chunks.append(c)

            content = b''.join(chunks)

        # --------------------------------------------------------------
        # 6. 后面的协议暂时保持你的原代码
        # --------------------------------------------------------------
        ba = bytearray(content)

        if len(ba) < 12:

            self.logger.error(
                "Decoded image is too short: %d bytes [%s]",
                len(ba),
                imgUrl
            )

            return False

        if ba[0] != 0 or ba[1] != 0:

            self.logger.error(
                "First bytes of binary from [%s] are wrong: "
                "%02x %02x",
                imgUrl,
                ba[0],
                ba[1]
            )

            return False

        # --------------------------------------------------------------
        # 7. 从 BMI magic header 获取 bookId
        # --------------------------------------------------------------
        bookId = (
            ba[2] * 256 +
            ba[3]
        )

        # --------------------------------------------------------------
        # 8. 获取 pageNumber
        # --------------------------------------------------------------
        pageNumber = (
            ba[4] * 16777216 +
            ba[5] * 65536 +
            ba[6] * 256 +
            ba[7]
        )

        self.logger.debug(
            "BMI image [%s]: bookId=%d, pageNumber=%d",
            imgUrl,
            bookId,
            pageNumber
        )

        # --------------------------------------------------------------
        # 9. 计算切片数量
        # --------------------------------------------------------------
        corpCount = self.getCorpCount(
            bookId,
            pageNumber
        )

        self.logger.debug(
            "BMI image [%s]: corpCount=%d",
            imgUrl,
            corpCount
        )

        # --------------------------------------------------------------
        # 10. 恢复 JPG magic number
        # --------------------------------------------------------------
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

        # --------------------------------------------------------------
        # 11. 重新排列切片并保存
        # --------------------------------------------------------------
        return self.regularateImageAndSave(
            ba,
            corpCount,
            targetImgPath
        )


if __name__ == '__main__':

    a = WuwuhanmanFetcher(
        '',
        ''
    )

    a.setInternalParameters(
        'https://www.55comic.com/book/4966',
        '繼母與繼姐',
        119
    )

    links = a.getChapterLinks()

    print(links)

    a.fetchImagesFromChapterPage(
        'https://www.55comic.com/free-chapter/43158?t=20260415',
        120,
        '/home/kzhang/github/comicViewer/comic/'
        '00-连载中/繼母與繼姐/120/'
    )

    # 测试单张图片时，可以使用：
    #
    # a.setInternalParameters(
    #     'https://www.55comic.com/free-chapter/46369?t=20260415'
    # )
    #
    # 注意：
    # 单独直接调用 downloadImg() 时，
    # self.bmiManifests 里没有 manifest。
    # 因此应该先通过 getImageLinksFromChapterPage()
    # 解析章节页面。

