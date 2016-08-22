import urllib
import urllib.request
import pprint
import collections
import re
import json

# Retrieving Maximum Number of IDs 
def search_max(myInput):
    testSearch = urllib.request.urlopen('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=1&sort=date&term=' \
                                        + myInput).read().decode("utf-8")
    # print(testSearch)
    # print(isinstance(testSearch, str))
    m = re.search('"count": "(.+?)",', testSearch)
    retMax = m.group(1)
    print('Search for "' + myInput + '" returned ' + retMax + ' PubMed records')
    return retMax

# Retrieving list of IDs by JSON parsing 
def myJson_function(inputTerm, numbRet):
    myJson = json.loads(urllib.request.urlopen('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=' \
                                               + numbRet + '&sort=date&term=' + inputTerm).read().decode("utf-8"))
    print('Is Dictionary?: ' + str(isinstance(myJson, dict)))  # Test if Dictionary: TRUE
    idList = myJson['esearchresult']['idlist'] # IT WORKS! extracts list object from dictionary
    print('Is List?: ' + str(isinstance(idList, list)))
    # print(idList)
    print('Final List Length: ' + str(len(idList)))
    return idList

# Getting Abstracts using list of PubMed IDs 
def getAbtracts(myTerm, retCustom, idList):
    myAbstracts = ['']
    n = 0
    for i in range(int(retCustom)):
        with urllib.request.urlopen('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=text&rettype=abstract&id=' \
                                    + idList[n]) as response:
            bbb = response.read().decode("utf-8")
            aaa = bbb.replace('\n', ' ').replace('.', ' ').replace(',', ' ').replace('(', ' ').replace(')', ' ') # Removes "\n" and other from
            myAbstracts.append(aaa)
            n = n + 1
    myAbstring = str(myAbstracts)
    if isinstance(myAbstring, str):
        print('The text IS string')
    else:
        print(' The text is NOT string')
    # Save as File final list    + '.txt'
    with open(myTerm + '.txt', 'w') as f: 
        f.write(str(myAbstring.encode("utf-8")))
        f.close()
    myUPString = myAbstring.upper() # Convert string into upper case
    abstrList = myUPString.split() # Splits string into a list of words
    # print(abstrList)
    abstrDict = collections.Counter(abstrList) # Creates dictionary with worrds as keys and their frequencies as values
    # pprint.pprint(abstrDict)
    print('The length of the ' + myTerm + ' dictionary is :' + str(len(abstrDict)))
    return abstrDict



# Getting First Term 

print('Enter first term of search:')
myTerm1 = input() # Later it Will be replaced with opening .csv file with list of top scores

retMax1 = search_max(myTerm1) # call of function to determine retMax 

print('Enter a number of abstracts (out of ' + retMax1 + ') to retrieve for "' + myTerm1 + '":')
retCustom1 = input()

idList1 = myJson_function(myTerm1, retCustom1) # Calling function to retrieve ID list
print(idList1)

# Getting Second Term 

print('Enter Second Term of Search:')
myTerm2 = input() # Later it Will be replaced with opening .csv file with list of top scores

retMax2 = search_max(myTerm2) # call of function to determine retMax2 for second term 

print('Enter a number of abstracts (out of ' + retMax2 + ') to retrieve for "' + myTerm2 + '":')
retCustom2 = input()

idList2 = myJson_function(myTerm2, retCustom2)
print(idList2)

# Getting Abstracts with list of PubMed IDs 
abstrDict1 = getAbtracts(myTerm1, retCustom1, idList1)
# print(abstDict1)

abstrDict2 = getAbtracts(myTerm2, retCustom2, idList2)
# print(abstDict2)

# Getting Literature Dictionary 

# This Segment gets text from https://www.gutenberg.org/  and converts it into dictionary
myLitra = urllib.request.urlopen('http://www.gutenberg.org/cache/epub/14577/pg14577.txt').read().decode("utf-8")
myLitraClean = myLitra.replace('"', ' ').replace('.', ' ').replace(':', ' ').replace('?', ' ').replace('_', ' ').replace(',', ' ').replace('(', ' ').replace(')', ' ')
myUPLitra = myLitraClean.upper() # Convert string into upper case
myLitraList = myUPLitra.split() # Splits string into a list of words
myLitraDict = collections.Counter(myLitraList) # Creates dictionary with worrds as keys and their frequencies as values
print('The length of the common Literature dictionary is :' + str(len(myLitraDict)))


# Subtracting Literature Dictionary 
#set - other - ...
cleanAbstr1 = set(abstrDict1.keys()) - set(myLitraDict.keys()) #  Return a new set with elements in the set that are not in the other.
pprint.pprint(cleanAbstr1)

print('The length of the Literature-cleaned ' + myTerm1 + ' dictionary is :' + str(len(cleanAbstr1)))

cleanAbstr2 = set(abstrDict2.keys()) - set(myLitraDict.keys()) #  Return a new set with elements in the set that are not in the other.
pprint.pprint(cleanAbstr2)


# Intersection of Two Terms 
  
#intersection(other, ...) # Return a new set with elements common to the set and all others.
#set & other & ...

finalAbstr1 = cleanAbstr1 & cleanAbstr2
pprint.pprint(finalAbstr1)
