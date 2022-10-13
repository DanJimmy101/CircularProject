# from asyncio.windows_events import NULL
import glob
import re
import nltk
from nltk.corpus import stopwords
from pathlib import Path
import json
from math import log2
import time
import os.path
from fastapi import APIRouter
import schedule
import csv

from utility import toignore, docfile, wordfile, wordlocfile, crawlPath, docCategoryPath

class FileIndexing:

    def __init__(self, doclist, wordlist, wordloclist, docCategoryPath):
        self.docfile = doclist
        self.wordfile = wordlist
        self.wordlocfile = wordloclist
        self.docCategoryPath = docCategoryPath
        self.avgdl = 0
        self.numdocs = 0
        content = {}
        self.lstDocCategory = []        
        self.lstDoc = []

        # if files are not made, then make them
        if not Path(doclist).is_file():
            with open(self.docfile, 'w', encoding='utf-8') as outfile:
                json.dump(content, outfile, default=self.jdefault, indent=4)

        if not Path(wordlist).is_file():
            with open(self.wordfile, 'w', encoding='utf-8') as outfile:
                json.dump(content, outfile, default=self.jdefault, indent=4)

        if not Path(wordloclist).is_file():
            with open(self.wordlocfile, 'w', encoding='utf-8') as outfile:
                json.dump(content, outfile, default=self.jdefault, indent=4)
        
        if Path(self.docCategoryPath).is_file():
            with open(self.docCategoryPath, encoding='utf-8') as docCategory:
                reader = csv.reader(docCategory, delimiter="\t")
                self.lstDocCategory = list(reader)
        
        self.lstDoc = [i[0] for i in self.lstDocCategory]

    def jdefault(self, o):
        return o.__dict__

    def get_text_only(self, textdata):
        # removing non alpha-numeric terms
        splitter = re.compile('\\W+')
        mp = splitter.split(textdata)
        tokens = [s.lower() for s in mp if s != '']
        # stemming the terms
        ps = nltk.stem.PorterStemmer()
        stemmed = []
        for words in tokens:
            stemmed.append(ps.stem(words))
        # returning the list of stemmed words
        return stemmed

    def crawl(self, dirname):
        print("Checking for new files")
        # pr = "./programming/"
        pr = dirname
        with open(self.docfile, 'r+', encoding='utf-8') as json_data:
            doclist = json.load(json_data)
        with open(self.wordfile, 'r+', encoding='utf-8')as json_data:
            wordlist = json.load(json_data)
        with open(self.wordlocfile, 'r+', encoding='utf-8') as json_data:
            wordloclist = json.load(json_data)
        if len(doclist) > 0 and doclist['dirname'] != pr:
            doclist = {}
            wordlist = {}
            wordloclist = {}
            doclist['dirname'] = pr
        else:
            if len(doclist) == 0:
                doclist['dirname'] = pr
        for file in glob.glob(pr + "*.txt"):
            url = file
            if url in doclist:
                # modifiedtime = time.ctime(os.path.getmtime(url))
                # if modifiedtime == doclist[url]['lastmodtime']:
                continue
            # print('a')           
            with open(url, 'r', encoding='utf-8') as f:
                counter = 1
                wordcounter = 0
                docCategory = ""
                docYear = None
                docSize = 0
                
                for count, doc in enumerate(self.lstDoc):
                    if doc == Path(url).name:
                        docCategory = self.lstDocCategory[count][1]
                        docSize = self.lstDocCategory[count][2]
                        break
                # print(time.time())

                for str1 in f:
                    if not docYear:
                        matchObj = re.search('\d{2}[ ]?\/[ ]?\d{4}', str1)
                        if matchObj:
                            matchVal = matchObj.group()
                            docYear = matchVal.split('/')[1].strip()

                    words = self.get_text_only(str1)

                    for word in words:
                        wordcounter += 1
                        if word in toignore:
                            continue

                        if word in wordlist:
                            if url in wordlist[word]:
                                wordlist[word][url] += 1
                            else:
                                wordlist[word][url] = 1
                                wordlist[word]["predoc"] += 1

                            if url in wordloclist[word]:
                                wordloclist[word][url].append([wordcounter, counter])
                            else:
                                wordloclist[word][url] = []
                                wordloclist[word][url].append([wordcounter, counter])
                        else:
                            wordlist[word] = {}
                            wordlist[word]["predoc"] = 1
                            wordlist[word][url] = 1

                            wordloclist[word] = {}
                            wordloclist[word][url] = []
                            wordloclist[word][url].append([wordcounter, counter])

                    counter += 1
                doclist[url] = {}
                doclist[url]['wordcount'] = wordcounter
                doclist[url]['Category'] = docCategory
                doclist[url]['Year'] = docYear
                doclist[url]['Size'] = docSize
                doclist[url]['lastmodtime'] = time.ctime(os.path.getmtime(url))
                

        with open(self.docfile, 'w', encoding='utf-8') as outfile:
            json.dump(doclist, outfile, default=self.jdefault, indent=4)
        with open(self.wordfile, 'w', encoding='utf-8') as outfile:
            json.dump(wordlist, outfile, default=self.jdefault, indent=4)
        with open(self.wordlocfile, 'w', encoding='utf-8') as outfile:
            json.dump(wordloclist, outfile, default=self.jdefault, indent=4)
        print("Indexing Complete")

def main():
    '''main function, calls other functions'''
    cp = FileIndexing(docfile, wordfile, wordlocfile, docCategoryPath)
    startindextime = time.time()
    cp.crawl(crawlPath)
    endindextime = time.time()
    print("Indexing completed in %f seconds" % (endindextime-startindextime))


if __name__ == '__main__':
    main()

# cp = FileIndexing(docfile, wordfile, wordlocfile, docCategoryPath)
# startindextime = time.time()
# cp.crawl(crawlPath)
# endindextime = time.time()
# print("Indexing completed in %f seconds" % (endindextime-startindextime))

schedule.every(1).minutes.do(main)

while True:
    schedule.run_pending()
    time.sleep(1)