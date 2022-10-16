# from asyncio.windows_events import NULL
from contextlib import nullcontext
from operator import le
import re
import nltk
from nltk.corpus import stopwords
from pathlib import Path
import json
import os
from math import log2
import time
from autocorrect import spell
from fastapi import APIRouter

from Models.searchresult import searchresult
from utility import docfile, wordfile, wordlocfile, localFileServerPath

class Search:
    def __init__(self, doclist, wordlist, wordloclist):
        with open(doclist, 'r', encoding='utf-8') as json_data:
            self.doclist = json.load(json_data)
        with open(wordlist, 'r', encoding='utf-8') as json_data:
            self.wordlist = json.load(json_data)
        with open(wordloclist, 'r', encoding='utf-8') as json_data:
            self.wordloclist = json.load(json_data)
        self.list_querywords = {}
        self.doc_for_phrasequery = {}
        self.stemmed = []

    def get_text_only(self, textdata, correction=True):
        splitter = re.compile('\\W+')
        xp = splitter.split(textdata)
        tokens = [s.lower() for s in xp if s != '']
        # print(tokens)
        # if correction:
        #     correctedtoken = []
        #     refinedquery = ""
        #     anychange = False
        #     for word in tokens:
        #         xp = spell(word)
        #         # print(xp,word)
        #         if xp != word:
        #             anychange = True
        #         refinedquery = refinedquery + " " + xp
        #         correctedtoken.append(xp)
        #     if anychange:
        #         confirm = input("Did u mean :"+refinedquery+" ? Enter 'y' to confirm...")
        #         if confirm == 'y':
        #             tokens = correctedtoken
        self.list_querywords =tokens
        ps = nltk.stem.PorterStemmer()
        stemmed = []
        for words in tokens:
            stemmed.append(ps.stem(words))
        if not correction:
            return tokens, stemmed
        self.stemmed = stemmed
        return stemmed

    def total_length(self):
        numdocs = len(self.doclist) - 1
        summation = 0
        for x, y in self.doclist.items():
            if x == 'dirname':
                continue
            summation = summation + y['wordcount']
        avgdl = float(summation/float(numdocs))
        return avgdl, numdocs

    def query(self, q, year, category):
        # self.phrasequery(q, year, category, printing=False)
        words = self.get_text_only(q)
        start_time = time.time()
        # words = self.stemmed
        doclist = {}
        linelist = {}
        nqlist = {}
        lll = len(words)

        for word in words:
            if word in self.wordlist:
                nqlist[word] = len(self.wordloclist[word])
                pos = self.wordloclist[word]
                for docs in pos:
                    if docs in doclist:
                        if word in doclist[docs]:
                            continue
                        else:
                            linenum = [x[1] for x in pos[docs]]
                            linelist[docs].append(linenum)
                            doclist[docs][word] = pos[docs]
                    else:
                        if year and category:
                            lstCategory = self.doclist[docs]['Category'].split(',')
                            isInlstCategory = False
                            for cat in lstCategory:
                                if category == cat.strip():
                                    isInlstCategory = True
                                    break
                            if self.doclist[docs]['Year'] == str(year) and  isInlstCategory:
                                doclist[docs] = {}
                                linelist[docs] = []
                                linenum = [x[1] for x in pos[docs]]
                                linelist[docs].append(linenum)
                                doclist[docs][word] = pos[docs]
                        elif year:
                            if self.doclist[docs]['Year'] == str(year):
                                doclist[docs] = {}
                                linelist[docs] = []
                                linenum = [x[1] for x in pos[docs]]
                                linelist[docs].append(linenum)
                                doclist[docs][word] = pos[docs]
                        elif category:
                            lstCategory = self.doclist[docs]['Category'].split(',')
                            isInlstCategory = False
                            for cat in lstCategory:
                                if category == cat.strip():
                                    isInlstCategory = True
                                    break
                            if isInlstCategory:
                                doclist[docs] = {}
                                linelist[docs] = []
                                linenum = [x[1] for x in pos[docs]]
                                linelist[docs].append(linenum)
                                doclist[docs][word] = pos[docs]
                        else:
                            doclist[docs] = {}
                            linelist[docs] = []
                            linenum = [x[1] for x in pos[docs]]
                            linelist[docs].append(linenum)
                            doclist[docs][word] = pos[docs]

            else:
                nqlist[word] = 0
        # print(linelist)
        if len(doclist) == 0:
            print("Not found!!")
            return []
        scoring = self.partialokapi(doclist=doclist, nqlist=nqlist, querylen=lll)
        finallines = {}
        for doc in doclist:
            finallines[doc] = self.unionlists(linelist[doc])
            # print(doc, finallines[doc])
        sortscore = sorted(scoring, key=scoring.get, reverse=True)
        # print(sortscore)
        pq = "file://"
        numberofdoc = len(sortscore)
        end_time = time.time()
        print("Found %d results in %f seconds\n" % (numberofdoc, end_time-start_time))
        counter = 0
        # print(sortscore)
        lstSearchResult = []
        # print("sooooooooooooooooorttttttttttscooooorrrrrreeeee")
        # print(sortscore)
        for x in sortscore:
            id=''
            filename=''
            path='',
            lines=''
            # if counter == 10:
            #     usercomm = input("Press 'y' to see next 20 results...\n")
            #     if usercomm == 'y':
            #         counter = 0
            #     else:
            #         return

            # x[x.index('-')+1:]
            filename = os.path.splitext(os.path.basename(x))[0]
            id = filename
            # id = filename[0:endindex]
            path = filename + '.pdf'
            # path = localFileServerPath + filename + '.pdf'
            # print("filename : ", (filename))
            # print("Path : ", (path))
            # print("\nLine Numbers :")
            # for word in doclist[x]:
            #     print(self.list_querywords[word]+" : ", [y[1] for y in doclist[x][word]])
            # if x in self.doc_for_phrasequery:
            #     print("Query found together at linenumber(s) :", self.doc_for_phrasequery[x])
            linecounter = 0
            with open(x, 'r',encoding='utf-8') as f:
                xp = f.readlines()
                # print('CATTTTTTTTTTTTTTTTTTTTTTTt')
                # print(finallines)
                for i in finallines[x]:
                    linecounter += 1
                    print_line = ''
                    line_string = xp[i-1]
                    # finallist, stemmedw = self.get_text_only(line_string, correction=False)
                    # print(finallist)

                    if linecounter <= 3:
                        # print(line_string)
                        lines = lines + line_string
                    # wcounter = 0
                    # for word in stemmedw:
                    #     if word in self.stemmed:
                    #         print_line = print_line + "\033[93m " + finallist[wcounter] + "\033[00m"
                    #     else:
                    #         print_line = print_line + " " + finallist[wcounter]
                    #     wcounter += 1
                    # if found:
                    # print("Line number " + str(i) + " :" + print_line)
            lstSearchResult.append(searchresult(id, filename, lines, path, self.doclist[x]['Year'], self.doclist[x]['Size']))
            # print("Score : ", scoring[x])
            # # print("\n")
            # print('------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
            # print('------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
            counter += 1
        return lstSearchResult

    def intersectlists(self, lists):
        if len(lists) == 0:
            return []
        # start intersecting from the smaller list
        lists.sort(key=len)
        # print lists
        mm = set(lists[0]).intersection(*lists)
        return list(mm)

    def unionlists(self, lists):
        if len(lists) == 0:
            return []
        mm = set().union(*lists)
        return sorted(list(mm))

    def phrasequery(self, q, year, category, printing=True):
        words = self.get_text_only(q)
        start_time = time.time()
        doclist = {}
        nqlist = {}
        wordll=[]
        locationdict = {}
        # lll = len(words)
        for word in words:
            if word in self.wordlist:
                filteredDoc = []
                app = [x for x in self.wordlist[word] if x != 'predoc']
                # filteredDoc.append(app)
                for doc in app:
                    if year and category:
                        lstCategory = self.doclist[doc]['Category'].split(',')
                        isInlstCategory = False
                        for cat in lstCategory:
                            if category == cat.strip():
                                isInlstCategory = True
                                break
                        if self.doclist[doc]['Year'] == str(year) and  isInlstCategory:
                            filteredDoc.append(doc)
                    elif year:
                        if self.doclist[doc]['Year'] == str(year):
                            filteredDoc.append(doc)
                    elif category:
                        lstCategory = self.doclist[doc]['Category'].split(',')
                        isInlstCategory = False
                        for cat in lstCategory:
                            if category == cat.strip():
                                isInlstCategory = True
                                break
                        if isInlstCategory:
                            filteredDoc.append(doc)
                    else:
                        filteredDoc.append(doc)
                wordll.append(filteredDoc)
            else:
                if printing:
                    print("Not found!!")
                return []
        # print(wordll)
        finaldocs = self.intersectlists(wordll)
        # print(finaldocs)

        for word in words:
            nqlist[word] = len(self.wordloclist[word])
            pos = self.wordloclist[word]
            for docs in finaldocs:
                if docs not in doclist:
                    doclist[docs] = {}
                # print(pos[docs])
                doclist[docs][word] = pos[docs]
        # newdoclist = copy.deepcopy(doclist)
        results = {}
        linenum = {}
        for docs in doclist:
            counter = 0
            dummy = []
            for word in words:
                for x in doclist[docs][word]:
                    locationdict[x[0]] = x[1]
                    x[0] = x[0] - counter
                # doclist[docs][word][0] = [(x-counter) for x in doclist[docs][word][0]]
                dummy.append([x[0] for x in doclist[docs][word]])
                counter += 1
            resultant = self.intersectlists(dummy)
            if len(resultant) == 0:
                continue
            else:
                # print(resultant)
                linenum[docs] = [locationdict[x] for x in resultant]
                results[docs] = len(resultant)
        if printing is False:
            self.doc_for_phrasequery = linenum
            return
        print("PHRASE QUERY")
        if len(results) == 0:
            print("Nothing found")
            # return 0
            return []
        scoring = self.phraseokapi(doclist=results)
        sortscore = sorted(scoring, key=scoring.get, reverse=True)
        # print(sortscore)
        pq = "file://"
        numberofdoc = len(sortscore)
        end_time = time.time()
        print("Found %d results in %f seconds\n" % (numberofdoc, end_time-start_time))
        lstSearchResult = []
        for x in sortscore:
            id=''
            filename=''
            path=''
            lines=''
            # print("filename : ", (pq + x))
            # print("line number(s) :", linenum[x])
            filename = os.path.splitext(os.path.basename(x))[0]
            id = filename
            path = filename + '.pdf'
            linecounter = 0
            with open(x, 'r',encoding='utf-8') as f:
                xp = f.readlines()
                for i in linenum[x]:
                    linecounter += 1
                    print_line = ''
                    line_string = xp[i-1]
                    # print(line_string)
                    # finallist, stemmedw = self.get_text_only(line_string, correction=False)
                    # print(finallist)

                    if linecounter <= 3:
                        lines = lines + line_string
                    # wcounter = 0
                    # for word in stemmedw:
                    #     if word in self.stemmed:
                    #         print_line = print_line + "\033[93m " + finallist[wcounter] + "\033[00m"
                    #     else:
                    #         print_line = print_line + " " + finallist[wcounter]
                    #     wcounter += 1
                    # if found:
                    # print("Line number "+ str(i) +" :"+print_line)
                lstSearchResult.append(searchresult(id, filename, lines, path, self.doclist[x]['Year'], self.doclist[x]['Size']))
            # print("Score : ", scoring[x])
            # print('----------------------------------x--------------------------------------------------------------------------------------------------------------------------------------------------------------------')
            # print('------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
        # return numberofdoc, (end_time-start_time)
        return lstSearchResult

    def phraseokapi(self, doclist, k=1.2, b=0.75, delta=1.0):
        avgdl, n = self.total_length()
        counts = dict([(docid, 0) for docid in doclist])
        val = len(doclist)
        for docs in doclist:
            doc_length = int(self.doclist[docs]['wordcount'])
            numerator = (k + 1) * doclist[docs]
            denominator = doclist[docs] + k * (1 - b + b * (doc_length / avgdl))
            idf = log2(n/val)
            score = idf * (delta + numerator / denominator)
            counts[docs] = score
        ncounts = self.normalizescores(counts)
        return ncounts

    def normalizescores(self, scores, smallisbetter=0):
        vsmall = 0.00001  # Avoid division by zero errors
        if smallisbetter:
            minscore = min(scores.values())
            return dict([(u, float(minscore) / max(vsmall, l)) for (u, l) in scores.items()])
        else:
            maxscore = max(scores.values())
            if maxscore == 0:
                maxscore = vsmall
            return dict([(u, float(c) / maxscore) for (u, c) in scores.items()])

    def partialokapi(self, doclist, nqlist, querylen, k=1.2, b=0.75, delta=1.0):
        avgdl, n = self.total_length()
        # print(avgdl, N)
        counts = dict([(docid, 0) for docid in doclist])

        for docid, values in doclist.items():
            score = 0.0
            counter = 0.0
            # print(values)
            doc_length = int(self.doclist[docid]['wordcount'])
            # print(doc_length)
            for dictionarywords in values:
                counter += 1.0
                numerator = (k + 1) * len(values[dictionarywords])
                # print(N, nqlist[dictionarywords])
                denominator = len(values[dictionarywords]) + k * (1 - b + b * (doc_length / avgdl))
                idf = log2(n/(nqlist[dictionarywords]))
                score += idf * (delta + numerator / denominator)
            counts[docid] = score*counter/(3*querylen)
        ncounts = self.normalizescores(counts)
        return ncounts

    def filterDocumentsByYearAndCategory(self, lstDocs, year, category):
        filteredDoc =  []
        for doc in lstDocs:
            if year and category:
                lstCategory = self.doclist[doc]['Category'].split(',')
                isInlstCategory = False
                for cat in lstCategory:
                    if category == cat.strip():
                        isInlstCategory = True
                        break
                if self.doclist[doc]['Year'] == str(year) and  isInlstCategory:
                    filteredDoc.append(doc)
            elif year:
                if self.doclist[doc]['Year'] == str(year):
                    filteredDoc.append(doc)
            elif category:
                lstCategory = self.doclist[doc]['Category'].split(',')
                isInlstCategory = False
                for cat in lstCategory:
                    if category == cat.strip():
                        isInlstCategory = True
                        break
                if isInlstCategory:
                    filteredDoc.append(doc)
            else:
                filteredDoc.append(doc)
        return filteredDoc

    def getDocsForPhraseQuery(self, phrase):
        wordll=[]
        doclist = {}
        words = self.get_text_only(phrase)
        locationdict = {}
        # print(words)
        for word in words:
            if word in self.wordlist:
                docsArr = []
                app = [x for x in self.wordlist[word] if x != 'predoc']
                for doc in app:
                    docsArr.append(doc)
                wordll.append(docsArr)
            else:
                return {}, {}

        finaldocs = self.intersectlists(wordll)

        for word in words:
            pos = self.wordloclist[word]
            for docs in finaldocs:
                if docs not in doclist:
                    doclist[docs] = {}
                # print(pos[docs])
                doclist[docs][word] = pos[docs]
            # newdoclist = copy.deepcopy(doclist)

        results = {}        
        linenum = {}
        for docs in doclist:
            counter = 0
            dummy = []
            for word in words:
                for x in doclist[docs][word]:
                    locationdict[x[0]] = x[1]
                    x[0] = x[0] - counter
                # doclist[docs][word][0] = [(x-counter) for x in doclist[docs][word][0]]
                dummy.append([x[0] for x in doclist[docs][word]])
                counter += 1
            resultant = self.intersectlists(dummy)
            if len(resultant) == 0:
                continue
            else:
                # print(resultant)
                linenum[docs] = [locationdict[x] for x in resultant]
                results[docs] = len(resultant)
        
        return  results, linenum

    def getDocsForQuery(self, query):
        wordll=[]
        linelist = {}
        words = self.get_text_only(query)
        # print(words)
        for word in words:
            if word in self.wordlist:
                pos = self.wordloclist[word]
                app = [x for x in self.wordlist[word] if x != 'predoc']
                for doc in app:
                    linelist[doc] = []
                    if doc not in wordll:
                        wordll.append(doc)
                        linenum = [x[1] for x in pos[doc]]
                        linelist[doc].extend(linenum) 

        return wordll, linelist

    def advancedQuery(self, include, phrase, exclude, year, category):
        # print(phrase)
        # print(include)
        # phraseAndIncludeDocs = []
        phraseAndIncludeDocsIntersect = []
        finalDocs = []
        wordDocs = []
        includeDocs = []
        excludeDocs = []
        linenum = {}
        linenumPhrase={}
        linenumDoc={}

        if phrase:
            wordDocs, linenumPhrase = self.getDocsForPhraseQuery(phrase)
            # print("Phrasedocs")
            wordDocs = self.filterDocumentsByYearAndCategory(wordDocs, year, category)
            # print(wordDocs)
            if len(wordDocs) > 0:
                # phraseAndIncludeDocs.append(wordDocs)
                linenum.update(linenumPhrase)

        if include:
            includeDocs, linenumDoc = self.getDocsForQuery(include)
            # print("Includedocs")
            # print(includeDocs)
            includeDocs = self.filterDocumentsByYearAndCategory(includeDocs, year, category)
            if len(includeDocs) > 0:
                # phraseAndIncludeDocs.append(includeDocs)
                if len(linenum) > 0:
                    for k, v in linenumDoc.items():
                        if k in linenum.keys():
                            for val in v:
                                if val in linenum[k]:
                                    continue
                                else:
                                    linenum[k].append(val)
                        else:
                            linenum[k] = [v]
                else:
                    linenum.update(linenumDoc)

        # phraseAndIncludeDocs = self.intersectlists(phraseAndIncludeDocs)

        if phrase and include:
            if len(wordDocs) > 0 and len(includeDocs) > 0:
                wordAndIncludeDocs = []
                wordAndIncludeDocs.append(wordDocs)
                wordAndIncludeDocs.append(includeDocs)             
                phraseAndIncludeDocsIntersect = self.intersectlists(wordAndIncludeDocs)
                # print("phraseAndIncludeDocsIntersect")
                # print(phraseAndIncludeDocsIntersect)  
        elif phrase:
            phraseAndIncludeDocsIntersect = wordDocs
        elif include:
            phraseAndIncludeDocsIntersect = includeDocs

        if exclude:
            excludeDocs, excludeDocsLineNum = self.getDocsForPhraseQuery(exclude)
            if len(phraseAndIncludeDocsIntersect) > 0:
                for phraseAndIncludeDoc in phraseAndIncludeDocsIntersect:
                    if phraseAndIncludeDoc not in excludeDocs:
                        finalDocs.append(phraseAndIncludeDoc)     
            else:
                if len(excludeDocs) > 0:
                    for doc in self.doclist:
                        if doc == 'dirname':
                            continue
                        else:
                            if doc not in excludeDocs:
                                finalDocs.append(doc)  
            
            finalDocs= self.filterDocumentsByYearAndCategory(finalDocs, year, category)
        else:
            for phraseAndIncludeDoc in phraseAndIncludeDocsIntersect:
                finalDocs.append(phraseAndIncludeDoc)

        # print(wordDocs)
        # print(includeDocs)
        # print(excludeDocs)
        # print(phraseAndIncludeDocsIntersect)
        # print(finalDocs)

        lstSearchResult = []
        for x in finalDocs:
            id=''
            filename=''
            path=''
            lines=''
            # print("filename : ", (pq + x))
            # print("line number(s) :", linenum[x])
            # print("BBBBBBBBBBBBBBBBBBBBBBBBB")
            # print(x)
            # print(linenumPhrase)
            # print(linenumDoc)
            # print(linenum)
            filename = os.path.splitext(os.path.basename(x))[0]
            id = filename
            path = filename + '.pdf'
            linecounter = 0
            with open(x, 'r',encoding='utf-8') as f:
                # print(x)
                xp = f.readlines()
                # if not exclude and include or phrase:
                if len(linenum) > 0:
                    for i in linenum[x]:
                        linecounter += 1
                        print_line = ''
                        line_string = xp[i-1]
                        # print(line_string)
                        # finallist, stemmedw = self.get_text_only(line_string, correction=False)
                        # prin(finallist)

                        if linecounter <= 3:
                            lines = lines + line_string
                        # wcounter = 0
                        # for word in stemmedw:
                        #     if word in self.stemmed:
                        #         print_line = print_line + "\033[93m " + finallist[wcounter] + "\033[00m"
                        #     else:
                        #         print_line = print_line + " " + finallist[wcounter]
                        #     wcounter += 1
                        # if found:
                        # print("Line number "+ str(i) +" :"+print_line)
                    # print(lines)
                lstSearchResult.append(searchresult(id, filename, lines, path, self.doclist[x]['Year'], self.doclist[x]['Size']))
                # else:                    
                #     lstSearchResult.append(searchresult(id, filename, '', path, self.doclist[x]['Year'], self.doclist[x]['Size']))
                
            # print("Score : ", scoring[x])
            # print('----------------------------------x--------------------------------------------------------------------------------------------------------------------------------------------------------------------')
            # print('------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
        # return numberofdoc, (end_time-start_time)
        return lstSearchResult

        print(linenumPhrase)
        print(linenumDoc)
# def stemmer(tokens):
#     ps = nltk.stem.PorterStemmer()
#     stemmed = []
#     for words in tokens:
#         stemmed.append(ps.stem(words))
#     return stemmed

def main():
    '''main function, calls other functions'''
    docfile = "doclist.txt"
    wordfile = "wordfile.txt"
    wordlocfile = "wordlocfile.txt"
    sp = Search(docfile, wordfile, wordlocfile)
    query = input('Please enter your query (enclose under "." for full-phrase query)....')
    if query != '':
        # print('You queried for "%s"  : ' % query)
        if query.startswith('"') and query.endswith('"'):
            # sp.advancedQuery("population", None, None, None, None)
            # sp.advancedQuery(None, "elders identity", None, None, None)
            # sp.advancedQuery(None, None, "public", None, None)
            # sp.advancedQuery( "population", "elders identity",None, None, None)
            sp.advancedQuery( "relief", "salary increments","III", None, None)

        else:
            sp.query("ensurance", None, None)

if __name__ == '__main__':
    main()

# @router.get("/runner/searchFiles")
# def searchFiles():
#     sp = Search(docfile, wordfile, wordlocfile)
#     query = input('Please enter your query (enclose under "." for full-phrase query)....')
#     if query != '':
#         print('You queried for "%s"  : ' % query)
#         if query.startswith('"') and query.endswith('"'):
#             sp.phrasequery(query)
#         else:
#             sp.query(query)

