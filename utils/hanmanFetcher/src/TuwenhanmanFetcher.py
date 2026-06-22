from BaseFetcher import BaseFetcher
import re
import json

class KamuFetcher(BaseFetcher):
    def __init__(self, comicRootPath, webSiteName, prefix = ''):
        super().__init__(comicRootPath, webSiteName, prefix)
        #self.proxy = {
        #    'http': 'http://192.168.119.47:8080',
        #    'https': 'http://192.168.119.47:8080'
        #}


    def login(self):
        host = "tuwenhanman.com"
        loginPostData = {
            "action": "login",
            "keeptime": str(3600 * 24),
            "gourl": ("https://%s/" % host),
            "user_name": "cruslefrat",
            "user_pwd": "9gU9CNBhMWH7Azd"
        }
        loginUrl = "https://%s/member/ajax_login.php?" % host
        firstPara = True
        for key in loginPostData.keys():
            if not firstPara:
                loginUrl = loginUrl + "&"
            else:
                firstPara = False
            loginUrl = loginUrl + ("%s=%s" % (key, loginPostData[key]))
        headers = json.loads(self.baseHttpHeadersStr)
        headers['Host'] = host
        r = self.httpClient.post(loginUrl, headers= headers, proxies=self.proxy)
        if r.status_code != 200:
            self.logger.error("Fail to login [%s]" % loginUrl)
            return False
        return True

    def parseComicWebToGetComicName(self, soup):
        h1 = soup.find('h1', attrs = {"class": "fed-part-eone fed-font-xvi"})
        if h1 == None:
            self.logger.error("Fail to get <h1> from soup [%s]" % self.comicLink)
            return ''
        a = h1.find('a')
        if a == None:
            self.logger.info("Fail to get <a> under <h1> [%s]" % self.comicLink)
            return ''
        return a.string


    def parseComicWebToGetChapterLinks(self, soup):
        aList = soup.find_all('a', attrs = {'class': 'fed-btns-info fed-rims-info fed-part-eone'})
        finalChapterLink = ''
        maxChapterIdx = -1
        chapterLinks = {}
        for a in aList:
            chapterIdx = -1
            for content in a.contents:
                nums = re.findall('第\s*(\d+)', str(content))
                if len(nums) > 0:
                    chapterIdx = int(nums[0])
                    if chapterIdx > maxChapterIdx:
                        maxChapterIdx = chapterIdx
                finalChapterKeys = re.findall('最终话', str(content))
                if len(finalChapterKeys) > 0:
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
        contentDiv = soup.find('div', attrs = {'style': 'max-width:720px;margin:0 auto;text:center;'})
        if contentDiv == None:
            self.logger.info("Fail to get <div style='max-width:720px;margin:0 auto;text:center;'> from soup")
            return []
        imgs = contentDiv.find_all('img')
        vipImg = list(filter(lambda x:x['src'].find('vip.png') >=0, imgs))
        if len(vipImg) > 0:
            self.logger.info("This page is for VIP, not fetch image")
            return []
        imgLinks = list(map(lambda x: x['src'], imgs))
        return imgLinks


if __name__ == '__main__':
    a = KamuFetcher('../test/', '图文韩漫')
    a.setInternalParameters('https://tuwenhanman.com/plus/list-656.html', '', 52)
    a.fetchComic()