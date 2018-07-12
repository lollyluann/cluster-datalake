import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np
import random
from generate_token_dict import DFS
import pandas as pd
import nltk, re, os, codecs, mpld3, sys
from time import time
from six import string_types
from sklearn.cluster import KMeans
from sklearn.externals import joblib
from sklearn import feature_extraction
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import MDS
from nltk.stem.snowball import SnowballStemmer
from mpl_toolkits.mplot3d import Axes3D

#=========1=========2=========3=========4=========5=========6=========7=

''' PARAM: a string containing the directory of .txt files
    RETURNS: a list of filenames and a list of the contents of the files 
    DOES: gets all the filenames and their contents of a directory'''   
def get_document_contents(directory):
    filenames = []
    data = []
    # for every file in the given directory
    print("num files in directory: ", len(os.listdir(directory)))
    i = 1
    for filename in os.listdir(directory):
        print(i)
        i = i + 1
        current_file = os.path.join(directory,filename)
        if os.path.isfile(current_file):
            # add the filename to "filenames" 
            filenames.append(filename)
            # read the contents of the file and remove newlines
            freader = open(current_file, "r", errors='backslashreplace')
            contents = freader.read()#.encode("utf-8").decode('utf-8', 'backslashreplace')
            freader.close()
            contents = contents.replace("\n","")
            # add the string of the contents of the file to "data"
            data.append(contents)
    print("Directory contents retrieved")
    return filenames, data

''' PARAM: the text of a document
    RETURN: list of stems
    DOES: splits a document into a list of tokens & stems each token '''
def tokenize_and_stem(text):
    # tokenize by sentence, then by word so punctuation is its own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out tokens without letters (e.g., numbers, punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token) 
    stemmer = SnowballStemmer("english")
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems

''' PARAM: the text of a document
    RETURN: a list of filtered tokens
    DOES: tokenizes the document only (doesn't stem) '''
def tokenize_only(text):
    # tokenize by sentence, then by word so punctuation is its own token
    tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out tokens without letters (e.g., numbers, punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    return filtered_tokens

#=========1=========2=========3=========4=========5=========6=========7=

def main_function(num_clusters, retokenize, corpusdir):
    # record initial time that program started
    t0 = time()

    # gets the filenames and their contents
    fnames, dataset = get_document_contents(corpusdir)
    #stopwords = nltk.download('stopwords')

    #nltk.download('punkt')
    # stemmer = SnowballStemmer("english")

    #=========1=========2=========3=========4=========5=========6=======

    if retokenize == "1": 
        totalvocab_stemmed = []
        totalvocab_tokenized = []
        count = 1
        d_length = len(dataset)
        for i in dataset:
            print("tokenizing document ", count, " of ", d_length)
            count = count + 1
            # for each item in the dataset, tokenize/stem
            allwords_stemmed = tokenize_and_stem(i)
            # extend "totalvocab_stemmed" 
            totalvocab_stemmed.extend(allwords_stemmed)
            
            # for each item in the dataset, tokenize only
            allwords_tokenized = tokenize_only(i)
            totalvocab_tokenized.extend(allwords_tokenized)

        # create vocab_frame with "totalvocab_stemmed" or "totalvocab_tokenized"
        vocab_frame = pd.DataFrame({'words': totalvocab_tokenized}, 
                    index = totalvocab_stemmed)
        vocab_frame.to_pickle("vocab_frame.pkl")
        print('there are ' + str(vocab_frame.shape[0]) + ' items in vocab_frame')

        #define vectorizer parameters
        tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=200000,
                              min_df=0.2, stop_words='english', use_idf=True, 
                              tokenizer=tokenize_and_stem, ngram_range=(1,3))

        #fits the vectorizer to the dataset
        tfidf_matrix = tfidf_vectorizer.fit_transform(dataset) 
        terms = tfidf_vectorizer.get_feature_names()
        np.save("terms.npy", terms)
        dist = 1 - cosine_similarity(tfidf_matrix)
        np.save("distance_matrix.npy", dist)
        print("vectorizer fitted to data")

        #=========1=========2=========3=========4=========5=========6======

        # cluster using KMeans on the tfidf matrix
        km = KMeans(n_clusters=num_clusters)
        km.fit(tfidf_matrix)
        clusters = km.labels_.tolist()
        print("kmeans clustering complete")

        # pickle the model, reload the model/reassign the labels as the clusters
        joblib.dump(km,  'doc_cluster.pkl')


    km = joblib.load('doc_cluster.pkl')
    vocab_frame = pd.read_pickle("vocab_frame.pkl")
    terms = np.load("terms.npy")
    dist = np.load("distance_matrix.npy")
    print("Loaded in existing cluster profile...\n")

    clusters = km.labels_.tolist()

    # create a dictionary "db" of filenames, contents, and clusters
    db = {'filename': fnames, 'content': dataset, 'cluster': clusters}
    # convert "db" to a pandas datafram
    frame = pd.DataFrame(db, index=[clusters], columns=['filename','cluster'])
    # print the number of files in each cluster
    print(frame['cluster'].value_counts())

    #=========1=========2=========3=========4=========5=========6=========
    '''  
    # open file writer for result output
    output_path = os.path.join(corpusdir, "results/")
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    os.chdir(output_path)
    fwriter = open("doc_clusters.txt", "w")
    fwriter.write("clusters from .txt files in: " + corpusdir)

    fwriter.write("\nTop terms per cluster: \n\n")
    print("Top terms per cluster: \n")

    #sort cluster centers by proximity to centroid
    order_centroids = km.cluster_centers_.argsort()[:, ::-1] 

    # for each cluster
    for i in range(num_clusters):
        fwriter.write("Cluster " + str(i) + " words: ")
        print("Cluster %d words:" % i, end='')
        
        # print the first "n_words" words in a cluster
        n_words = 10
        for ind in order_centroids[i, : n_words]:
            print(' %s' % vocab_frame.ix[terms[ind].split(' ')].values.tolist()[0][0],
                    end=",")
            fwriter.write(vocab_frame.ix[terms[ind].split(' ')].values.tolist()[0][0].rstrip('\n') + ", ")
        print()
        fwriter.write("\n")
        
        # print out the filenames in the cluster
        print("Cluster %d filenames:" % i, end='')
        fwriter.write("Cluster " + str(i) + " filenames: ")
        for filename in frame.ix[i]['filename'].values.tolist():
            print(' %s,' % filename, end='')
            fwriter.write(filename.rstrip('\n') + ", ")
        print("\n")
        fwriter.write("\n\n")

    fwriter.close()
    print("output written to \"doc_clusters.txt\" in \"results\" of the original directory")

    #=========1=========2=========3=========4=========5=========6========

    # multidimensional scaling to convert distance matrix into 3 dimensions
    mds = MDS(n_components=3, dissimilarity="precomputed", random_state=1)
    pos = mds.fit_transform(dist)  # shape (n_components, n_samples)
    xs, ys, zs = pos[:, 0], pos[:, 1], pos[:, 2]

    # set up plot
    fig = plt.figure(figsize=(17,9))
    ax = Axes3D(fig)

    # create data frame with MDS results, cluster numbers, and filenames
    df = pd.DataFrame(dict(x=xs, y=ys, z=zs, label=clusters, filename=fnames)) 
    # group by cluster
    groups = df.groupby('label')
    colors = ["#cc1b00", "#d9ca00", "#40ff40", "#4d9994", "#003d73", "#180059", "#59434f", "#a6877c", "#a6a37c", "#1a331a", "#40bfff", "#bfc8ff", "#a6299d", "#59161f", "#b2862d", "#549926", "#bfffd0", "#0088ff", "#3d3df2", "#d9a3ce", "#ff8091"]
    # for each cluster, plot the files in that cluster
    i = 0
    for name, group in groups:
        # color = ('#%06X' % random.randint(0,256**3-1))
        # color = np.random.rand(3,)
        for t in range(group.shape[0]):
            ax.scatter(group.x.iloc[t], group.y.iloc[t], group.z.iloc[t], 
                c=colors[i], marker='o')
            ax.set_aspect('auto')
        i+=1

    plt.savefig("3D_document_cluster", dpi=300)
    print("scatter plot written to \"3D_document_cluster.png\"")
    
    # print total time taken to run program
    print("time taken: ", time()-t0)
    '''
    return frame


def bar_clusters(frame, path, num_clusters):
    file_pathtokens_dict, file_path_dict = DFS(path,1)
    plt.figure("hist")
    
    for i in range(num_clusters):
        plt.clf()
        paths_in_cluster = {}
        print(frame.loc[frame['cluster']==1])
        count = 0    
        for row in frame.loc[frame['cluster']==i]:
            if count>1:
                print(row)
                fna = row['filename']
                path = file_path_dict.get(fna)
                if path in paths_in_cluster:
                    paths_in_cluster.update({path:paths_in_cluster.get(path)+1})
                else:
                    paths_in_cluster.update({path:1})
            count+=1
        sorted_names = []
        sorted_counts = []
        for e in sorted(paths_in_cluster, key=paths_in_cluster.get, reverse=True):
            sorted_names.append(e)
            sorted_counts.append(paths_in_cluster[e])
        y_pos = np.arange(len(sorted_names))

        plt.bar(y_pos, sorted_counts, align='center', alpha=0.5)
        plt.xticks(y_pos, sorted_names)
        plt.ylabel('Number of files')
        plt.title('Directories in Cluster ' + str(i))
        save_name = "histogram_cluster"+str(i)
        os.chdir("/home/ljung/CDIAC-clust/txt_cluster_hists/")
        plt.savefig(save_name, dpi=200)


# MAIN PROGRAM

num_clusters = int(sys.argv[1])
retokenize = sys.argv[2]
# the directory of the files you want to cluster
corpusdir = "/home/ljung/extension_sorted_data/all_text/"
corpusdir = sys.argv[3]
fr = main_function(num_clusters, retokenize, corpusdir)
#bar_clusters(fr, "/home/ljung/pub8/", num_clusters)