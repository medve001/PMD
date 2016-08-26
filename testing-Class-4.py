'''
GOAL: Extracting text of abstracts, titles and keywords from XML output of PubMed. 

TO DO:
0. Titles and Keywords to Dictionaries
1. Merge with "testing-XML-parsing-with-ElementTree-3.py"
2. Merge with "Third List" code
3. Merge with "Random splite" code
4. Merge with "Master Code"

Next Level of Analysis
5. Add Tanimoto similarity check to 
6. Add Phys-Chem data from PubChem
7. Cluster Analysis of the list using number of PubMed IDs of the pairs as distance (1/len(id_list))
8. Use all_drugs_list, bio_terms_list, etc to identify meaningful terms in the list

'''

import csv
import requests
import xml.etree.ElementTree
import json
import datetime
import time
import sqlite3
import collections

time_start = datetime.datetime.now()  # Time Started


# ======== Classes ===============

class Chemical:
    def __init__(self, name, ret_init='max'):
        self.name = name
        self.ret_init = ret_init
        self.ret_max = Chemical.get_ret_max(self, name)
        self.ret_number = Chemical.set_ret_custom(self, ret_init)
        self.id_list = Chemical.get_id_list(self, self.ret_number)

    def print_name(self):
        print(self.name)

    def set_ret_custom(self, ret_init):

        if ret_init == 'max':
            ret_number = self.ret_max
        else:
            ret_number = ret_init
        return ret_number

    def get_name(self):
        return self.name

    def get_ret_max(self, name):
        resp = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=1&sort=date&term={}'.format(name))
        ret_dict = json.loads(resp.text)
        ret_max = ret_dict['esearchresult']['count']
        return ret_max

    def get_id_list(self, ret_number):

        resp = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax={}&sort=date&term={}'.format(ret_number, self.name))
        ret_dict = json.loads(resp.text)
        id_list = ret_dict['esearchresult']['idlist']
        print('Number of IDs in the {} list is {}'.format(self.name, len(id_list)))
        return id_list


# ======== Functions =========================

def pair_intersect(num1, num2):
    # Finding Intersection between two lists
    set12 = set(chemicals[num1].id_list) & set(chemicals[num2].id_list)
    set1 = set(chemicals[num1].id_list) - set12
    set2 = set(chemicals[num2].id_list) - set12
    return list(set1), list(set2), list(set12)


def db_update(id_list):
    # Grouping  id_list items for PubMed query
    group_list = []
    for n in range(0, len(id_list), 50):
        tmp = id_list[n:(n + 50)]
        print(tmp)
        group_list.append(','.join(tmp))

    # Fetching Abstracts by groups of ids
    for id_group in group_list:
        response = requests.get(
            'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&rettype=medline&id={}'.format(id_group))
        bbb = response.text
        # print(bbb)
        root = xml.etree.ElementTree.fromstring(bbb)

        for pub_art in root.findall('.//PubmedArticle'):

            # Extracting PMID
            id_node = pub_art.find('.//PMID')
            id_text = id_node.text

            # Extracting Abstract
            ab_node = pub_art.find('.//AbstractText')
            try:
                ab_text = ab_node.text
            except AttributeError:
                print('The record id = {} has no abstract'.format(id_text))
                ab_text = 'no abstract'
            ab_clean = ab_text.replace('\n', ' ').replace('.', ' ').replace(',', ' ').replace('(', ' ').replace(')', ' ')

            # Extracting Article Title
            at_node = pub_art.find('.//ArticleTitle')
            at_title = at_node.text
            at_clean = at_title.replace('\n', ' ').replace('.', ' ').replace(',', ' ').replace('(', ' ').replace(')', ' ')

            # Extracting Keywords
            my_keywords = []
            for node in pub_art.findall('.//Keyword'):
                my_keywords.append(node.text)
            keywords_str = ', '.join(my_keywords)

            # Inserting results into database (if not exist)
            try:
                c.execute("INSERT INTO abstracts VALUES(?, ?, ?, ?)", (id_text, at_clean, ab_clean, keywords_str))
                # conn.commit()
            except sqlite3.IntegrityError:
                print('The record already exists')
            except AttributeError:
                print('The record id = {} has problem and was not inserted'.format(id_text))
        conn.commit()
        time.sleep(0.5)


# Fetching specific columns from database
def db_fetch(id_list, column):
    word_list = []
    for id_fetch in id_list:
        c.execute("SELECT {} FROM abstracts WHERE id={}".format(column, id_fetch,))  # star means "select all"
        row = str(c.fetchone())
        #print(row)
        clean_line = row.replace('"', ' ').replace('.', ' ').replace(':', ' ').replace('?', ' ').replace('_', ' ').replace(',', ' ').replace('(', ' ').replace(')', ' ').replace(';', ' ')
        # print(clean_line)
        for word in clean_line.split():
            word_list.append(word.upper())
    word_dict = collections.Counter(word_list)
    return word_dict


##################################################
# =========== PROGRAM START  =====================
##################################################

# Connect to database
conn = sqlite3.connect('chemical_db.sqlite')
# Create cursor object
c = conn.cursor()
# Create Table of Abstracts if not exists
c.execute('CREATE TABLE IF NOT EXISTS abstracts(id TEXT UNIQUE, title TEXT, abstract TEXT, keywords TEXT)')
conn.commit()
# Create Table of Compounds if not exists
c.execute('CREATE TABLE IF NOT EXISTS compounds(name TEXT UNIQUE, id_count TEXT, id_list TEXT, cas TEXT)')
conn.commit()

# === Loading High Score Chemical List from csv file ===
chem_list = []
while True:
    try:
        search_term = input('What search term? (test1):')
        with open(search_term + '-score.csv') as csv_file:
            csv_dict = csv.DictReader(csv_file)
            for row_csv in csv_dict:
                chem_list.append(row_csv['Sample_ID'])
    except FileNotFoundError:
        print("Wrong file or file path")
    else:
        break
print('List to be analyzed: {}'.format(chem_list))

# ====== Automated Class instance list generation =======
# Generation of the list of class instances by list comprehension
mm = input('How many abstracts to retrieve(for testing, 0 = max)?\n')
chemicals = [Chemical(chem_list[chem_n], mm) for chem_n in range(len(chem_list))]

print('List of class instances was generated for: ')
for inst in chemicals:
    print("the {0.name} has {0.ret_max} records in PubMed".format(inst))

# ==== Updating compounds table in database ==========

for inst in chemicals:
    # Checks if chem is already in database
    # Adds abstracts to database if chem is not in database
    try:
        c.execute("INSERT INTO compounds VALUES(?, ?, ?, ?)", (inst.name.lower(), inst.ret_max, ','.join(inst.id_list), 'na',))
        conn.commit()
        db_update(inst.id_list)
    except sqlite3.IntegrityError:
        print('The record already exists')


id_list1, id_list2, id_list12 = pair_intersect(0, 1)  # Get lists for pair of chemicals
print('Overlap between {} and {} is {} publications'.format(chemicals[0].name, chemicals[1].name, len(id_list12)))

# ==== Creating Literature Dictionary ==========
lit_file_list = ['pg14577.txt', 'pg52017.txt', 'pg52019.txt']
litra_list = []
for file in lit_file_list:
    with open(file, 'r') as f:
        for line in f.readlines():
            clean_line = line.replace('"', ' ').replace('.', ' ').replace(':', ' ').replace('?', ' ').replace('_', ' ').replace(
                ',', ' ').replace('(', ' ').replace(')', ' ').replace(';', ' ')
            # print(clean_line)
            for word in clean_line.split():
                litra_list.append(word.upper())

print(len(litra_list))
litra_dict = collections.Counter(litra_list)

# ==== Fetching Abstracts from database =======
atrazine_dict = db_fetch(id_list1, 'abstract')

# print(atrazine_dict)
print(len(atrazine_dict))

# ==== Fetching Keywords from database =======
atrazine_key_dict = db_fetch(id_list1, 'keywords')

# print(atrazine_key_dict)
print(len(atrazine_key_dict))



'''
Subtracting literature

Questions:
Article titles and keywords separately?

Handling chem pair overlapping abstracts

Final data presentation, tweaking
'''




# ====== Time Stamp ====================
time_finish = datetime.datetime.now()  # Time Finished
print('\nProgram started: {}, finished: {}'.format(time_start, time_finish))
print('\nProgram run time:')
print(time_finish - time_start)



'''
Try these functions for debugging
    type()
    dir()
    id()
    getattr()
    hasattr()
    globals()
    locals()
    callable()

To Do: Check this article
http://stackoverflow.com/questions/11685936/python-attributeerror-object-has-no-attribute
'''
