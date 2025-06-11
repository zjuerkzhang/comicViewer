from BaseFetcher import BaseFetcher
import re

class KamuFetcher(BaseFetcher):
    def __init__(self, comicRootPath, webSiteName):
        super().__init__(comicRootPath, webSiteName)


    def parseComicWebToGetComicName(self, soup):
        div = soup.find('div', attrs = {"class": "cy_title"})
        if div == None:
            self.logger.info("Fail to get <div class='cy_title'> from soup %s" % self.comicLink)
            return ''
        h1 = div.find('h1')
        if h1 == None:
            self.logger.info("Fail to get <div class='cy_title'>.<h1> from soup %s" % self.comicLink)
            return ''
        return h1.string


    def parseComicWebToGetChapterLinks(self, soup):
        liList = soup.find_all('li', attrs = {'class': 'chapter__item'})
        finalChapterLink = ''
        maxChapterIdx = -1
        chapterLinks = {}
        for li in liList:
            a = li.find('a')
            if a == None:
                self.logger.info("No <a> under <ls>" % li.prettify())
                continue
            chapterIdx = -1
            for content in a.contents:
                nums = re.findall('第\s*(\d+)', str(content))
                if len(nums) > 0:
                    chapterIdx = int(nums[0])
                    if chapterIdx > maxChapterIdx:
                        maxChapterIdx = chapterIdx
                finalChapterKeys = re.findall('最終話', str(content))
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
        contentDiv = soup.find('div', attrs = {'class': 'rd-article-wr clearfix'})
        if contentDiv == None:
            self.logger.info("Fail to get <div class='rd-article-wr clearfix'> from soup")
            return []
        imgs = contentDiv.find_all('img')
        imgLinks = list(map(lambda x: x['data-original'], imgs))
        return imgLinks


if __name__ == '__main__':
    a = KamuFetcher('../test/', '卡慕漫画')
    a.setInternalParameters('https://kamu.cc/comic/nuerguimidouguime', '', 62)
    a.fetchComic()