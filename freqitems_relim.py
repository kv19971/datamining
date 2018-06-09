from pymining import itemmining, assocrules
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

MINSUP = 100 #Minimum Support 
db = Model()


def getFrequentItems(transactions): #function to get frequent itemsets based on given transactions
    relim_input = itemmining.get_relim_input(transactions) #restructure transactions into relim input 
    item_sets = itemmining.relim(relim_input, MINSUP) #get itemsets with minimum support 
    results = []
    for k, v in item_sets.items(): #return results
        results.append(list(k))
    return results


results = getFrequentItems(db.getAllTransactions())

def fwritestring(lst): #helper function to write list of lists to file
    s = "\n".join([",".join([li for li in l]) for l in lst])
    return s

with open("relimout.txt", "w+") as fl:
    fl.write(fwritestring(results))


print("FINISHED")