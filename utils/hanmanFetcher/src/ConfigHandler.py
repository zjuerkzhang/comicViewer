import json

class ConfigHandler(object):
    def __init__(self, configFilePath):
        self.configFilePath = configFilePath
        jsonConfig = None
        with open(self.configFilePath, 'r') as f:
            jsonConfig = json.load(f)
        self.jsonConfig = jsonConfig


    def validateConfig(self):
        if self.jsonConfig == None or 'targetDir' not in self.jsonConfig.keys() or 'comics' not in self.jsonConfig.keys():
            return False
        return True


    def getConfig(self):
        return self.jsonConfig


    def dumpFile(self):
        with open(self.configFilePath, 'w') as f:
            json.dump(self.jsonConfig, f, indent = 4, ensure_ascii = False)


    def updateLatestChapterIdx(self, key, link, name, newIdx):
        for comic in self.jsonConfig['comics']:
            if key not in comic['links'].keys():
                continue
            if comic['links'][key] == link:
                comic['latestChapterIdx'] = newIdx
                comic['name'] = name
                break
        self.dumpFile()


    def insertNewComic(self, key, link):
        allLinks = []
        for c in self.jsonConfig['comics']:
            allLinks.extend(c['links'].values())
        #print(allLinks)
        if link in allLinks:
            return
        newComic = {
            'name': '',
            'links': {
                'hmk': '',
                'akhm': '',
                'kamu': '',
                'wuwu': ''
            },
            'latestChapterIdx': 0
        }
        newComic['links'][key] = link
        self.jsonConfig['comics'].append(newComic)
        self.dumpFile()
