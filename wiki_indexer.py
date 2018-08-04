from __future__ import print_function
import xml.etree.ElementTree as etree
import re
from collections import *
import sys
from Stemmer import Stemmer as PyStemmer
import os
import heapq
import math

reload(sys)
sys.setdefaultencoding('utf-8')
ps = PyStemmer('porter')
stopwords = {}
args = sys.argv
tags = {'title': 0, 'text': 1, 'category': 2}
print_tags = {'title': 't', 'text': 'p', 'category': 'c'}
dir_names = ["title", "text", "category"]
allwords = {}
occ = [defaultdict(int) for i in range(3)]
pathWikiXML = args[1]
document_number = 0
new_adj = [defaultdict(list) for i in xrange(0, 3)]
file_index = [0, 0, 0, 0]
total_document_count = 0
offset_pointer = []
offset_value = [0, 0, 0, 0]
document_titles = open('doc_titles.txt', 'wb')
posting_pointer = []

def strip_tag_name(t):
	idx = k = t.rfind("}")
	if idx != -1:
		t = t[idx + 1:]
	return t

# update dictionary for category
def update_dict_infobox(text): 
	tmpword = re.findall("{{Infobox(.*?)}}", text)
	if tmpword :
		for t in tmpword :
			t = t.split(' ')
			for temp in t: 
				temp = temp.lower()
				temp = ps.stemWord(temp)
				if (temp) and (temp not in stopwords):
					occ[3][temp] += 1
					allwords[temp] = 1

# update dictionary for category
def update_dict_category(text): 
	tmpword = re.findall("\[\[Category:(.*?)\]\]", text)
	if tmpword :
		for t in tmpword :
			t = t.split(' ')
			for temp in t: 
				temp = temp.lower()
				temp = ps.stemWord(temp)
				if (temp) and (temp not in stopwords):
					occ[2][temp] += 1
					allwords[temp] = 1
				
# update dictionary for title, text
def update_dict(tag_type, text):
	global occ, allwords, tags
	for word in re.split('[^A-Za-z0-9]', text):
		word = word.lower()
		word = ps.stemWord(word) 
		if (word != '') and (word not in stopwords) :
			occ[tags[tag_type]][word] += 1
			allwords[word] = 1
def writeIntoFile(tag_index, pathOfFolder, index, countFinalFile):                                        
    global posting_pointer
    data = []                                                                             #write the primary index
    for key in sorted(index):
        string = str(key)+' '
        temp = index[key]
        if len(temp) != 0:
            idf = math.log10(total_document_count / float(len(temp)))
        for i in range(len(temp)):
            S1 = temp[i].split('d')
            if len(S1) > 1:
                S2 = S1[1].split('c')
                if len(S2) > 1:
	                DD,CC = S2[0], float(S2[1])
	                GG = (1+math.log10(CC)) * idf
	                GG = ("%.2f" % GG)
	                string += 'd' + DD + 'c' + str(GG) + ' '

        data.append(string)
    	fileName = pathOfFolder + '/term_offset.txt'
        offset_pointer[tag_index].write(key + ":" + str(offset_value[tag_index]) + "\n")
        offset_value[tag_index] += 1 + len(string)
    
  
    posting_pointer[tag_index].write('\n'.join(data))
    posting_pointer[tag_index].write('\n')
    countFinalFile += 1

def mergeFiles(tag_index, pathOfFolder, countFile, f_name):                                                 #merge multiple primary indexes
    listOfWords, indexFile, topOfFile = {}, {}, {}
    flag = [0] * countFile
    data = defaultdict(list)
    heap = []
    countFinalFile = 0
    for i in xrange(countFile):
        fileName = pathOfFolder + f_name + str(i)
        indexFile[i] = open(fileName, 'rb')
        flag[i] = 1
        topOfFile[i] = indexFile[i].readline().strip()
        listOfWords[i] = topOfFile[i].split(':')
        if listOfWords[i][0] not in heap:
            heapq.heappush(heap, listOfWords[i][0])        
    count = 0        
    while any(flag) == 1:
        temp = heapq.heappop(heap)
        count += 1
        for i in xrange(countFile):
            if flag[i]:
                if listOfWords[i][0] == temp:
                    data[temp].extend(listOfWords[i][1:])
                    if count == 1000000:
                        oldCountFile = countFinalFile
                        writeIntoFile(tag_index, pathOfFolder, data, countFinalFile)
                        if oldCountFile != countFinalFile:
                            data = defaultdict(list)
                    topOfFile[i] = indexFile[i].readline().strip()   
                    if topOfFile[i] == '':
                            flag[i] = 0
                            indexFile[i].close()
                            os.remove(pathOfFolder + f_name + str(i))
                    else:
                        listOfWords[i] = topOfFile[i].split(':')
                        if listOfWords[i][0] not in heap:
                            heapq.heappush(heap, listOfWords[i][0])
    writeIntoFile(tag_index, pathOfFolder, data, countFinalFile)

# make a list of all the stopwords.
with open('stopwords.txt', 'r') as file :
	words = file.read().split('\n')
	# stem the stop word
	for word in words: 
		word = ps.stemWord(word)
		if word:
			stopwords[word] = 1

documentcount = 0
# parse the documents
for event, elem in etree.iterparse(pathWikiXML, events = ('start', 'end')):
	tag_name = strip_tag_name(elem.tag)

	# finished extracting all the text in the page tag.
	if (tag_name == 'page') and (event == 'end'): 
		documentcount += 1
		total_document_count += 1
		for word in allwords:
			for tag in tags: 
				if occ[tags[tag]][word] != 0: 
					node = 'd' + str(document_number) + 'c' + str(occ[tags[tag]][word])
					new_adj[tags[tag]][word].append(node)
		
		occ = [defaultdict(int) for i in range(3)]
		allwords = {}
		document_number += 1
		elem.clear()

	elif (tag_name in tags) and (event == 'end'): 
		if tag_name == 'text': 
			update_dict_category(str(elem.text))
			#  update_dict_infobox(str(elem.text))
		update_dict(tag_name, str(elem.text))
		if tag_name == 'title': document_titles.write(str(elem.text) + '\n') 

	if documentcount >= 2000: 
		documentcount = 0
		for i in range(3): 
			directory = dir_names[i]
			if not os.path.exists(str("./" + directory)): 
				os.makedirs(str("./" + directory))
			os.chdir(str("./" + directory))
			s = str(print_tags[dir_names[i]]) + str(file_index[i])
			f = open(s, "w")	
			for v in sorted(new_adj[i]): 
				s = v + ":"
				for u in new_adj[i][v]: 
					s += u + ":" 
				print(s, file = f) 
			f.close()
			os.chdir("../")
			file_index[i] += 1
		new_adj = [defaultdict(list) for i in xrange(0, 3)]

if documentcount > 0: 
	for i in range(3): 
		directory = dir_names[i]
		if not os.path.exists(str("./" + directory)): 
			os.makedirs(str("./" + directory))
		os.chdir(str("./" + directory))
		s = str(print_tags[dir_names[i]]) + str(file_index[i])
		f = open(s, "w")	
		for v in sorted(new_adj[i]): 
			s = v + ":"
			for u in new_adj[i][v]: 
				s += u + ":" 
			print(s, file = f) 
		f.close()
		os.chdir("../")
		file_index[i] += 1

offset_pointer.append(open("./title/term_offset.txt", 'wb'))
offset_pointer.append(open("./text/term_offset.txt", 'wb'))
offset_pointer.append(open("./category/term_offset.txt", 'wb'))


posting_pointer.append(open("./title/final.txt", 'wb'))
posting_pointer.append(open("./text/final.txt", 'wb'))
posting_pointer.append(open("./category/final.txt", 'wb'))


mergeFiles(0, "./title/", file_index[0], 't')
mergeFiles(1, "./text/", file_index[1], 'p')
mergeFiles(2, "./category/", file_index[2], 'c')

# code for query

for i in range(3): 
	offset_pointer[i].close()
	posting_pointer[i].close()
