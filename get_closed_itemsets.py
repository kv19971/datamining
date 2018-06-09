#for 2.2 
from collections import defaultdict

class Model: #Helper class to retrieve transactions from database and maintain single item count
    FILENAME = "freq_items_dataset.txt" #file with transactions
    def __init__(self): #load transactions from file into an array 
        self.items = set() #set of unique single items in db
        self.itemCountMap = defaultdict(lambda: 0) #dictionary to maintain count of all single items
        self.transactions = []
        with open(Model.FILENAME, "r") as fl:
            content = fl.read().split("\n")
            for row in content: #for each transaction
                temp = [r for r in row.split(" ") if r != ''] #split to get each item in given transaction
                for i in temp: #for each item
                    self.items.add(i) #add item to set of items (note that since we use python's in built set, duplicates are removed)
                    self.itemCountMap[i] += 1 #increment item count
                self.transactions.append(temp)
        self.items = list(self.items)
    
    def getAllTransactions(self): #return all transactions
        return self.transactions
    def getAllItems(self): #return all unique items in transactions
        return self.items
    def getSingleItemCount(self, name): #get support count for single item 
        return self.itemCountMap[name]

db = Model()

MINSUP = 100 #MINIMUM SUPPORT
FREQ_FILE = "output.txt"

# immediate superset should be a subset and diff of 1 element 
def getSupportCount(items, transactions): # get support count for given itemset in transactions
    if(len(items) == 1): #if itemset has only 1 item then use given function in Model class to get support
        (tmpel,) = items
        return db.getSingleItemCount(tmpel)
    else: #otherwise go through all transactions to calculate support for itemset
        cnt = 0
        for i, t in enumerate(transactions):
            if items.issubset(t): # if itemset is subset of transaction then increment support 
                cnt += 1 
        return cnt
transactions = db.getAllTransactions() #get all transactions from Model class
transactions = [frozenset(t) for t in transactions] #convert each transaction into set (to be able to do subset operation in getSupportCount)

#Load itemsets from previous output, convert each of them to a set, store them in a list 
freqitemsets = []
with open(FREQ_FILE, "r") as fl:  # output.txt - file containing frequent itemsets
    freqitemsets = fl.read().split("\n")
freqitemsets = [frozenset([fi for fi in f.split(",") if fi != '']) for f in freqitemsets]
freqitemsets = [f for f in freqitemsets if len(f) > 0]

#to put itemsets of different length in different groups, sort list by number of items in each itemset. 
freqitemsets.sort(key = lambda t: len(t)) 
#now we group itemsets based on length
categorized = {} #dictionary having list of itemsets of different lengths - key: length, value: list of itemsets with that length
freqCount = {} #dictionary maintaining support count for each frequent itemset

for f in freqitemsets: # for every itemset add it to its particular group - defined by the itemset's length 
    if len(f) not in categorized.keys():
        categorized[len(f)] = []
    categorized[len(f)].append(f)
    freqCount[f] = getSupportCount(f, transactions) # maintain support count for each frequent itemset 

tiers = len(categorized) # number of groups created - number of distinct itemset lengths 
itemsets_dict = {} #dictionary with key: itemset, value: list of itemsets that are immediate superset of key

def isImmediateSuperSet(smallset, largeset): #helper function to see if larger itemset is immediate superset of smaller itemset
    return smallset.issubset(largeset) and ((len(largeset) - len(smallset)) == 1)

for i in range(2, tiers+1): #for each possible length of itemset
    for c in categorized[i-1]: #for each itemset of length i-1
        itemsets_dict[c] = [] #initialize itemsets (c's) dictionary entry to store all immediate supersets
        for sc in categorized[i]: #then for each itemset of length i (as difference in size of immediate superset and set always 1)
            if isImmediateSuperSet(c, sc): #if itemset is immediate superset then add that to the list
                itemsets_dict[c].append(sc)
for c in categorized[tiers]: #for itemsets of max length, which can have no supersets, we initialize their dictionary entries too 
    itemsets_dict[c] = []

#now we iterate through all itemsets (in order of their size to identify whether they are maximal or closed or both)
results = [] #list storing (itemset, if itemset is closed, if itemset is maximal)
for i in range(1, tiers+1): #for all possible itemset lengths 
    for c in categorized[i]: # for each itemset of length i
        closed = True #assume itemset both closed and maximal 
        maximal = True
        itemsup = freqCount[c] # support for c
        for s in itemsets_dict[c]: # for all of c's immediate supersets 
            tmp = freqCount[s] # get s's support count
            if(tmp == itemsup): #s is c's immediate superset. if support for s == support for c then c is not closed
                closed = False
            if(tmp >= MINSUP): #if immediate superset's support is >= minimum support then at least one of c's immediate supersets is frequent 
                maximal = False
            if(closed == False and maximal == False): #optimization - if both are false then terminate 
                break
        results.append((c, closed, maximal))

#for r in results:
#    print(r)

#Write results to file
closed = [list(r[0]) for r in results if r[1] == True]
maximal = [list(r[0]) for r in results if r[2] == True]
both = [list(r[0]) for r in results if r[1] == True and r[2] == True]

def fwritestring(lst):
    s = "\n".join([",".join([li for li in l]) for l in lst])
    return s

with open("closedout2.txt", "w+") as fl:
    fl.write(fwritestring(closed))

with open("maximalout2.txt", "w+") as fl:
    fl.write(fwritestring(maximal))

with open("bothout2.txt", "w+") as fl:
    fl.write(fwritestring(both))



        

print("FINISHED")
