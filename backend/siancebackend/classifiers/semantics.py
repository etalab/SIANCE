
import sklearn.feature_extraction
from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop
from spacy.lang.en.stop_words import STOP_WORDS as en_stop

final_stopwords_list = list(fr_stop) #+ list(en_stop)
for word in ["asn", "demandes", "demande", "constats", "constat", "inspections", "inspection"]:
    final_stopwords_list.append(word)
# IDEE : one document = the corpus of all sentences attached to this label!

"""
def tokenize_and_stem(text):
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)

    #exclude stopwords from stemmed words
    stems = [stemmer.stem(t) for t in filtered_tokens if word not in stopwords]

    return stems
"""
from siancedb.models import (
    SessionWrapper,
    SiancedbPrediction,
    SiancedbLabel
)
from scipy.sparse import csr_matrix
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.cluster import (
    SpectralClustering,
    AgglomerativeClustering
)
import json

sentences = []
for id_label in range(700,770):
    with SessionWrapper() as db:
        print(db.query(SiancedbLabel.subcategory).filter(SiancedbLabel.id_label==id_label).one())
        print(len(list(db.query(SiancedbPrediction).filter(SiancedbPrediction.id_label==id_label))))
        
        sentences.append(
          " ".join([str(sent.sentence) for sent in db.query(SiancedbPrediction).filter(SiancedbPrediction.id_label==id_label).filter(SiancedbPrediction.id_model==23).all()][:20])   
        )
"""
sentences = [
     'This is the first document.',
     'This document is the second document.',
     'And this is the third one.',
     'Is this the first document?',
]
print(sentences)
"""
sentences_train, sentences_test = train_test_split(sentences, train_size=0.75, random_state=42)

vectorizer = sklearn.feature_extraction.text.TfidfVectorizer(
    input="content",
    use_idf=True,
    smooth_idf=True,
    #tokenizer=tokenize_and_stem,
    stop_words=final_stopwords_list   
)


x = vectorizer.fit_transform(sentences)
print("computed vectorizer")
coref = x.transpose().dot(x)
print("computed coref")

n_clusters = int(len( vectorizer.vocabulary_ ) / 20)
spectral = SpectralClustering(
    affinity="precomputed",
    n_clusters=n_clusters
)
agglomerative = AgglomerativeClustering(
    
)

path = "../../../../clusters.json"

def semantics(coreferences, vocabulary):
    inv_vocabulary = {v: k for k, v in vocabulary.items()}
    labels = spectral.fit_predict(coreferences)
    print("computed spectral")
    out = []
    for k in range(n_clusters):
        words_inds = np.where(labels==k)[0]
        words = [inv_vocabulary[word_ind] for word_ind in words_inds]
        print(words)
        out.append(words)
    with open(path, "w") as f:
        json.dump(out, f)
    
semantics(coref,  vectorizer.vocabulary_ )
# with open(classifier_path, "wb") as file:
#   pickle.dump(model, file)
# pickle.load(spectral)

def coref(x):
    coref_indices = coref.toarray().argsort(axis=1)
    #coref_couples = np.array(coref.argmax(axis=0))[0]

    top = 3

    for ind, coref_inds in enumerate(coref_indices):
        if (ind > 3):
            break
        words = np.flip(coref_inds[coref_inds!=ind][-top:])
        print(inv[ind], [inv[word] for word in words])
        print("***")    
