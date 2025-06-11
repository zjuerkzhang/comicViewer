from BaseFetcher import BaseFetcher
import re

class AikanhanmanFetcher(BaseFetcher):
    def __init__(self, comicRootPath, webSiteName):
        super().__init__(comicRootPath, webSiteName)


    def parseComicWebToGetComicName(self, soup):
        p = soup.find('p', attrs = {"class": "comic-title j-comic-title"})
        if p == None:
            self.logger.info("Fail to get <p> from soup [%s]" % self.comicLink)
            return ''
        return p.string


    def parseComicWebToGetChapterLinks(self, soup):
        aList = soup.find_all('a', attrs = {'class': 'j-chapter-link'})
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
                finalChapterFound = len(re.findall('最終話', str(content))) > 0 or len(re.findall('最终话', str(content))) > 0
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
        contentDiv = soup.find('div', attrs = {'class': 'rd-article-wr clearfix'})
        if contentDiv == None:
            self.logger.info("Fail to get <div class='rd-article-wr clearfix'> from soup")
            return []
        imgs = contentDiv.find_all('img')
        imgLinks = list(map(lambda x: x['data-original'], imgs))
        return imgLinks


if __name__ == '__main__':
    a = AikanhanmanFetcher('../test/', '爱看韩漫')
    a.setInternalParameters('https://www.aikanhanman.com/index.php/comic/ruzhuinuxu', '', 36)
    a.fetchComic()