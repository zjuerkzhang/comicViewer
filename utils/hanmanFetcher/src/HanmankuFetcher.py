from AikanhanmanFetcher import AikanhanmanFetcher

class HanmankuFetcher(AikanhanmanFetcher):
    def __init__(self, comicRootPath, webSiteName):
        super().__init__(comicRootPath, webSiteName)
        self.proxy = {
            'http': 'http://192.168.119.47:8080',
            'https': 'http://192.168.119.47:8080'
        }
        #self.proxy = None


if __name__ == '__main__':
    a = HanmankuFetcher('../test/', '韩漫库')
    a.setInternalParameters('https://se8.us/index.php/comic/tongyanjimu', '', 7)
    a.fetchComic()