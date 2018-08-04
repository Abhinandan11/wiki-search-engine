from __future__ import print_function
import xml.etree.ElementTree as etree
import re
from collections import *
import sys
from Stemmer import Stemmer as PyStemmer
import os
import heapq
import math
import operator
import string
import time

reload(sys)
sys.setdefaultencoding('utf-8')
ps = PyStemmer('porter')
stopwords = {}
inverted_index_file = []
inverted_index_file.append(open('./title/final.txt', 'r'))
inverted_index_file.append(open('./text/final.txt', 'r'))
inverted_index_file.append(open('./category/final.txt', 'r'))
dir_names = ["title", "text", "category"]
docs = defaultdict(float)
mapping = [defaultdict(int) for i in range(3)]
document_titles = open('doc_titles.txt', 'r')
doc_offset = []

def create_offset(): 
	lines = document_titles.readlines()
	cumulative = 0
	for line in lines: 
		doc_offset.append(cumulative)
		cumulative += len(line)

def index_term_mapping(i):
	mapping = defaultdict(int)
	os.chdir(dir_names[i])
	with open("term_offset.txt") as file:
		lines = file.readlines()
		for line in lines:
			line = line.split(':')
			mapping[line[0]] = int(line[1].strip())
	file.close() 
	os.chdir("../")
	return mapping

def single_field_query_tag(q, i): 
	global inverted_index_file, docs, mapping
	if q in mapping[i]: 
		off = mapping[i][q]
		inverted_index_file[i].seek(off)
		line = inverted_index_file[i].readline()
		line = line.split(' ')
		l = len(line)
		for word in line : 
			if word == q: continue
			word = word.split('d')
			if len(word) > 1:
				word = word[1].split('c')
				if len(word) > 1: 
					
					docs[word[0]] += float(word[1])

def single_field_query(q):
	for i in range(3): 
		single_field_query_tag(q, i)
	
def relevance_ranking():
	global docs
	Docs = sorted(docs.items(), key = operator.itemgetter(1), reverse = True)
	Docs = Docs[:min(10, len(docs))]
	for doc in Docs:
		t = int(doc_offset[int(doc[0])])
		document_titles.seek(t)	
		new_string = document_titles.readline().strip()
		output = string.replace(new_string, ' ', '_')
		print ("https://en.wikipedia.org/wiki/" + output)

# make a list of all the stopwords.
with open('stopwords.txt', 'r') as file :
	words = file.read().split('\n')
	# stem the stop word
	for word in words: 
		word = ps.stemWord(word)
		if word:
			stopwords[word] = 1

mapping[0] = index_term_mapping(0)
mapping[1] = index_term_mapping(1)
mapping[2] = index_term_mapping(2)
create_offset()

while True:
	query = raw_input("Query-> ").strip('\n').lower()
	start = time.time()
	flag = 0
	docs = defaultdict(float)
	if ("t:" in query) or ("d:" in query) or ("c:" in query) or ("i:" in query) or ("e:" in query):
		flag = 1
	query = query.split(' ')
	if flag: 
		for q in query:
			q = q.split(':')
			q[1] = ps.stemWord(q[1])
			if q[0] == "t":
				single_field_query_tag(q[1], 0)
			elif q[0] == "d":
				single_field_query_tag(q[1], 1)
			elif q[0] == "c":
				single_field_query_tag(q[1], 2)
			elif q[0] == "i":
				pass
			else:
				pass
	else :
		for q in query: 
			q = ps.stemWord(q)
			single_field_query(q)

	relevance_ranking()
	print ("Query time:", time.time() - start, "seconds.")	

for i in range(3): 
	inverted_index_file[i].close()
