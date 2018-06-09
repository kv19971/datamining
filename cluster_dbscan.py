#!usr/bin/python3
import math
import numpy as np
import scipy.io as scio
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as colors
from sklearn.cluster import DBSCAN ##INCLUDED TO COMPARE WITH SKLEARN RESULT - NOT USED IN PERSONAL IMPLEMENTATION

FILENAME = "DBSCAN-Points.mat"
OUTDIR = "dbscan_outs/" #directory in which output files will be stored

def doSKLearn(dataset, epsilon, minpoints):
    '''
    Method that takes the dataset, parameters epsilon and minpts
    returns None 
    Performs DBSCAN clustering on dataset and plots the result 
    '''
    db = DBSCAN(eps=epsilon, min_samples=minpoints) #Initialize model with parameters
    db.fit(dataset) #do clustering 
    cluster_labels = db.labels_ #array representing each point's (in dataset) cluster membership 
    unique_clusters = list(set(cluster_labels)) #get unique list of clusters created 
    n_clusters = len(unique_clusters) 
    title = "SKLEARN Implememtation, eps=0.12, minpts=3, finds 8 clusters"
    plt.title(title)
    for nc in unique_clusters: # for each cluster 
        cpoints = [p for i, p in enumerate(dataset) if cluster_labels[i] == nc] #get all points that belong to that cluster
        x = [p[0] for p in cpoints]
        y = [p[1] for p in cpoints]
        plt.scatter(x,y,  marker = "o" if nc >= 0 else "x") #plot these points
    plt.savefig(OUTDIR + title+".png", bbox_inches="tight")
    plt.clf()
    #plt.show() #show plot
   

class Point: 
    '''
    Helper point class 
    Each member in dataset needs to be a point before it can be processed by DBScan class
    Following labels possible:
        -2 - Undefined 
        -1 - Outlier
        1 ... n - belongs to cluster 1...n
    '''
    def __init__(self, x, y): #initialize point with given coordinates and undefined label
        self.x = x
        self.y = y
        self.label = -2 #undefined label
    def distanceWith(self, p2): #compute euclidian distance with another point 
        return math.sqrt(math.pow((p2.x - self.x), 2) + math.pow((p2.y - self.y), 2))
    def equals(self, p2):
        return self.x == p2.x and self.y == p2.y
    def resetLabel(self): #reset label to undefined
        self.label = -2
    def __str__(self): #for pretty printing 
        return str(self.x) + ", " + str(self.y)

class DBScan:
    '''
    DBScan class 
    class based implementation for DBScan algo 
    '''
    def __init__(self, dataset, epsilon, minpoints): #initialize model with dataset and parameters 
        self.dataset = dataset # assume dataset is a list of points 
        self.resetDataset() #clear previous labels 
        self.epsilon = epsilon
        self.minpoints = minpoints
        self.clusters = 0
    def rangeQuery(self, p): #returns list of points that are close to given point p (within euclidian distance of self.epsilon)
        neighbors = []
        for p2 in self.dataset:
            if(p.distanceWith(p2) <= self.epsilon):
                neighbors.append(p2)
        return neighbors
    def runScan(self): #run DBScan algorithm on dataset
        for p in self.dataset: # for every point 
            if p.label != -2:  # if label is defined then skip it (as it has been processed in one of the previous iterations)
                continue
            neighbors = self.rangeQuery(p) # get neighbors of point 
            if(len(neighbors) < self.minpoints): # if number of neighbors less than threshold then point is not a core point
                p.label = -1
                continue # skip that point as it will be assigned a cluster in one of the next iterations if it is a border point 
            self.clusters += 1 # add a cluster
            p.label = self.clusters # assign current point to that cluster 
            seedset = [n for n in neighbors if not(p.equals(n))] # seedset is points that are neighbors of p but not p 
            while(len(seedset) > 0): #While seedset is not empty
                n = seedset.pop() #get point from seedset 
                if(n.label == -1): #if that point has outlier label then assign it to current cluster 
                    n.label = self.clusters
                if(n.label != -2): #if that point's label is not undefined then skip it (as it has already been processed)
                    continue
                n.label = self.clusters #assign current point to the cluster 
                ns2 = self.rangeQuery(n) #get all points in the neighborhood of the current point 
                #to take care of candidate core points around current core point 
                if(len(ns2) >= self.minpoints): # if number of points in neighborhood is greater than the threshold then  
                    tmp = list(set(ns2) - set(seedset)) # get those points that are in this neighborhood but not in the current seedset 
                    for t in tmp:
                        seedset.append(t) #add them to the seedset 
    def getCmap(self): #Helper function to map a color to each cluster (for visualization )
        N = self.clusters
        color_norm  = colors.Normalize(vmin=0, vmax=N)
        scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='nipy_spectral') 
        def map_index_to_rgb_color(index):
            return scalar_map.to_rgba(index)
        return map_index_to_rgb_color
    def showResult(self, title = None): #plot clustered dataset 
        if(title is None):
            title = "DBSCAN RESULT"
        plt.title(title) #give plot title 
        cmap = self.getCmap() #get a mapping from cluster number to label
        for p in self.dataset:
            plt.scatter([p.x], [p.y], color=cmap(p.label), marker="x" if p.label == -1 else "o") #for each point plot it on graph with designated cluster's color
        plt.savefig(OUTDIR + title+".png", bbox_inches="tight")
        plt.clf()
        #plt.show()
    def getSilouetteCoeff(self): # method to compute average silouette coefficient over the entire dataset - intrinsic performance indicator 
        if(self.clusters == 0): # if no clusters created then 0 score 
            return 0
        cof_sum = 0
        for p in self.dataset: #for every point in dataset
            ai_sum = 0 # maintain sum for a(i) - average distance of point with other points in cluster 
            ai_c = 0 #maintain count for ai - how many points in cluster 
            if(p.label == -1): # if point is outlier then skip it 
                continue
            min_dists = [-1 for i in range(self.clusters)] # array to maintain list of minimum distances between point p and other clusters 
            #this is for b(i) - average of mimimum distance of point to other clusters
            for p2 in self.dataset: # for every other point 
                if(p2.label == -1): # if point outlier then skip over it 
                    continue
                if(p2.label == p.label): # if p2 is in the same cluster as p
                    ai_c += 1
                    ai_sum += p.distanceWith(p2) # add sum and count for a(i)
                else: #otherwise if p and p2 belong to different clusters 
                    ind = int(p2.label-1)
                    if(min_dists[ind] == -1 or min_dists[ind] > p.distanceWith(p2)): #get min distance with p2's cluster
                        min_dists[ind] = p.distanceWith(p2)
            bi = sum([d for d in min_dists if d != -1]) / max((len(min_dists)-1), 1) #compute b(i)
            ai = ai_sum/ai_c #compute a(i)
            cof = (bi-ai) / max(ai,bi) #get coefficient 
            cof_sum += cof # add to sum of coefficients
        return cof_sum/len(self.dataset) #return average coefficient 
    def resetDataset(self): #method to reset all labels in given dataset
        for d in dataset:
            d.resetLabel()    


dataset = scio.loadmat(FILENAME)["Points"] #load dataset

##for default parameters minpts=3 and eps = 0.12 
doSKLearn(dataset, 0.12, 3) #show sklearn result for reference 
dataset = [Point(t[0], t[1]) for t in dataset] #make dataset list of point objects for my implementation
dbscan = DBScan(dataset, 0.08, 2) #run my implementation 
dbscan.runScan()
dbscan.showResult("My Implementation, eps=0.12 minpts=3, finds "+str(dbscan.clusters) + "clusters") # show results 
print("For default params, coefficient:",dbscan.getSilouetteCoeff()) #show coefficient 
##for custom parameters 
minpts_params = [i for i in range(2, 6)] #possible minpts = 2...6
dist_params = [i/100 for i in range(8, 24, 4)] #possible eps = 0.08 ... 0.24
res = [['x' for i in range(len(dist_params) + 1)] for j in range(len(minpts_params) + 1)] #matrix to store avg coefficients for each set of parameters 
#add index rows and columns to res having parameters 
#so that user knows what coefficient values correspond to what parameters 
res[0][0] = 'x'
for i in range(len(dist_params)):
    res[0][i+1] = str(dist_params[i])
for i in range(len(minpts_params)):
    res[i+1][0] = str(minpts_params[i])

for i, pts in enumerate(minpts_params): #for every possible minpts param
    for j, eps in enumerate(dist_params): #for every possible eps param 
        dbscan2 = None
        dbscan2 = DBScan(dataset, eps, pts) #run dbscan and show result  
        dbscan2.runScan()
        dbscan2.showResult("For eps=" + str(eps) + " minpts=" + str(pts)+ " finds "+str(dbscan2.clusters) + "clusters")
        cof = (dbscan2.getSilouetteCoeff()) # compute average silouette coefficient 
        res[i+1][j+1] = str(cof) #add it to matrix 
       
print(res) #show coefficients 
with open(OUTDIR + "DBSCAN_RES.csv", "w+") as fw: #write coefficient results to file 
    out = "\n".join([",".join(r) for r in res])
    fw.write(out)
