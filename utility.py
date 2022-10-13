
import nltk
from nltk.corpus import stopwords

docfile = 'doclist.txt'
wordfile = 'wordfile.txt'
wordlocfile = 'wordlocfile.txt'
crawlPath = 'ScrapedPDFs/'
docCategoryPath = 'documentcategory.txt'
stopwordsNotToBeUsedPath = 'stopwords_not_to_be_used.txt'
localFileServerPath = 'http://127.0.0.1:8887/'

def stemmer(tokens):
    ps = nltk.stem.PorterStemmer()
    stemmed = []
    for words in tokens:
        stemmed.append(ps.stem(words))
    return stemmed

ignorewords = set(stopwords.words('english'))
toignore = stemmer(ignorewords)

