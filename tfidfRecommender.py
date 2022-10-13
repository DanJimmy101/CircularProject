# https://goodboychan.github.io/python/datacamp/natural_language_processing/2020/07/17/04-TF-IDF-and-similarity-scores.html

import nltk
from nltk.corpus import stopwords
import os
import random
import re
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
import joblib
import time
import json
from Models.searchresult import searchresult

from utility import crawlPath, docfile

#Use this function to create custom list of stop_words for your Project

def get_stopwords(path):
  stopwords = nltk.corpus.stopwords.words('english')
  not_words = []
  with open(path,'r', encoding='utf-8') as f:
    not_words.append(f.readlines())
  not_words = [word.replace('\n','') for words in not_words for word in words]
  not_words = set(not_words)
  stopwords = set(stopwords)
  customized_stopwords = list(stopwords - not_words)
  return stopwords,customized_stopwords

"""### Loading the Data"""

def load_data(path):
  # path='testPDF/'
  documents = []
  train_texts = []
  for fname in sorted(os.listdir(path)):
    if fname.endswith('.txt'):
      with open(os.path.join(path,fname), encoding="utf-8") as f:
        documents.append(fname)
        train_texts.append(f.read())
  return documents, train_texts


def load_data_for_uploaded_document(path, fname):
  train_text = []
  with open(os.path.join(path,fname),'r', encoding='utf-8') as f:
    train_text.append(f.read())
  return train_text

"""### Tokenizing the document and filtering the tokens"""

def tokenize(train_texts):
  filtered_tokens = []
  tokens = [word for sent in nltk.sent_tokenize(train_texts) for word in nltk.word_tokenize(sent)]
  for token in tokens:
    if re.search('[a-zA-Z]',token):
      filtered_tokens.append(token)
  return filtered_tokens


"""### Tokenizing and stemming using Snowball stemmer"""

def tokenize_stem(train_texts):
  tokens = tokenize(train_texts)
  stemmer = SnowballStemmer('english')
  stemmed_tokens = [stemmer.stem(token) for token in tokens]
  return stemmed_tokens


"""### Calculating Tf-idf matrix"""

'''
Attributes in TfidVectorizer are data dependent.
Use 'stop_words = customized_stopwords' if you want to use your own set of stopwords else leave it as it is.
Functions available for tokenizer -> 1)tokenize  2) tokenize_stem  3) Remove the attribute to use default function
'''

def tfid_vector(train_texts):
  tfidf_vectorizer = TfidfVectorizer(max_df = 0.85, min_df = 0.1, sublinear_tf = True, stop_words = 'english', use_idf = True, tokenizer = tokenize, ngram_range = (1,10))
  tfidf_matrix = tfidf_vectorizer.fit_transform(train_texts)
  # joblib.dump(tfidf_vectorizer, 'tfidf_vectorizer.pkl')

  return tfidf_matrix

def get_recommendations(documents, cosine_sim, indices, minVal, maxVal):
    # Get the index of article
    idx = [indices.index(document) for document in documents]
    # print('idx are')
    # print(idx)
    # Get the pairwsie similarity scores

    sim_scores_lst = []
    for i in range(len(idx)):
      sim_scores = list(enumerate(cosine_sim[idx[i]]))
      # print('sim_scores are')
      # print(sim_scores)

      for i in range(len(sim_scores)):
        sim_scores_lst.append(sim_scores[i])
       
    # print('sim_scores array are')
    # print(sim_scores_lst)
    
    # Sort the articles based on the similarity scores
    sim_scores = sorted(sim_scores_lst, key=lambda x: x[1], reverse=True)

    # print('sim_scores array sorted by desc are')
    # print(sim_scores)

    # Get the scores for  most similar articles
    sim_scores = sim_scores[len(documents):len(sim_scores)]
    
    # print(sim_scores)

    sim_scores = [sim_score for sim_score in sim_scores if minVal <= sim_score[1] <= maxVal]
 
    # print('**************************************************************************************')
    # print(sim_scores)
    # print('**************************************************************************************')

    article_indices = []
    i=0
    # Get the top 5 article indices
    for element in sim_scores:
      if(i==5):
        break
      if element[0] not in article_indices and element[0] not in idx:
        article_indices.append(element[0])
        # print(element[1])
        i=i+1

    doclistData = None
    with open(docfile, 'r', encoding='utf-8') as json_data:
            doclistData = json.load(json_data)
    
    # article_indicesa = [indices[i] for i in article_indices]
    # print(article_indicesa)

    lstRecommendations= []
    for x in article_indices:
      # print(indices[x])
      docPath = 'ScrapedPDFs\\' + indices[x]
      lstRecommendations.append(searchresult(None, indices[x], None, None, doclistData[docPath]['Year'], doclistData[docPath]['Size']))
    # Return the top  most similar articls
    return lstRecommendations

# def main():
def getRecommendations(clcikedDocuments, minVal, maxVal):
    '''main function, calls other functions'''
    startindextime = time.time()   
    documents, train_texts = load_data(crawlPath)
    # print(documents)
    # print(documents.index('Demand-Management-Schedule-from-03.08-to-05.08.2022-1659887076.9751575.txt'))
    tfidf_matrix = tfid_vector(train_texts)
    # print(tfidf_matrix)
    # Generate the cosine similarity matrix
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    # print(cosine_sim)
    # Generate recommendations
    lstRecommendations = get_recommendations(clcikedDocuments, cosine_sim, documents, minVal, maxVal)
    # print(lstRecommendations)
    endindextime = time.time()
    print("Recommendation completed in %f seconds" % (endindextime-startindextime))
    return lstRecommendations

def main():
    '''main function, calls other functions'''
    startindextime = time.time()
    
    lst = ['Agrahara Insurance Scheme for Public Officers-1664961694.3382146.txt']
    getRecommendations(lst, 0, 1)
    endindextime = time.time()
    print("recommendation completed in %f seconds" % (endindextime-startindextime))



if __name__ == '__main__':
    main()