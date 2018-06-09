from collections import defaultdict
import itertools


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

MINSUP = 1000 # minsup parameter 
db = Model()

def getKSubset(items, k): #get all k sized subsets of items (given in parameter items)
    return map(set, itertools.combinations(items, k))

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

#get pruned itemsets given transactions, unique items in those transactions and maximum width (i.e. how large the generated itemsets should be)
def getPrunedItemsets(items, transactions, width): 
    #make items and each transaction a set, to perform subset operations
    items = set(items) 
    transactions = [set(t) for t in transactions]

    finalsubsets = [] #store all pruned itemsets here

    for k in range(1,width+1): #for all possible widths from 1 to (width)
        subset = getKSubset(items, k) # get all k sized subsets from items
        
        #generate support count for each generated itemset, store as tuple with itemset in list
        subset = [(s, getSupportCount(s, transactions)) for s in subset] 
        subset = [t for t in subset if t[1] >= MINSUP] #pruning step - if support count less than minimum support then get rid of that itemset
        if(len(subset) == 0): #if no itemsets left after pruning then continue
            continue
        for sub in subset: #append remaining subsets to result 
            finalsubsets.append(sub)
        #from remaining subsets, get all unique single items, for next iteration
        subset = [t[0] for t in subset]
        items = set.union(*subset)
    return finalsubsets

print("")
print("There are " + str(len(db.getAllItems())) + "items in db")
results = getPrunedItemsets(db.getAllItems(), db.getAllTransactions(), 6)
#write results to file 
with open("aprout.txt", "w+") as fl: #write results to file
    fl.write("\n".join([",".join(r) for r in results]))
