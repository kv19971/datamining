#!usr/bin/python3 
import math 
import random
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as colors
import scipy.io as scio
from scipy.stats import multivariate_normal
import numpy as np 

FILENAME = "GMM-Points.mat"
OUTDIR = "emgmm_outs/"  #directory in which output files will be stored

class Point: 
    '''
    Helper point class 
    Each member in dataset needs to be a point before it can be processed by DBScan class
    Following labels possible:
        -1 - Undefined
        1 ... n - belongs to cluster 1...n
    '''
    def __init__(self, x, y): #initialize point with given coordinates and undefined label
        self.x = x
        self.y = y
        self.label = -1 #undefined label
        self.round = None # keep track of which round of emgmm youre performing - initially none
    def distanceWith(self, p2): #compute euclidian distance with another point 
        return math.sqrt(math.pow((p2.x - self.x), 2) + math.pow((p2.y - self.y), 2))
    def equals(self, p2):
        return self.x == p2.x and self.y == p2.y
    def resetLabel(self): #reset label to undefined
        self.label = -2
    def __str__(self): #for pretty printing 
        return str(self.x) + ", " + str(self.y)

class GaussianCluster:
    '''
    Helper gaussian cluster class - used to represent each gaussian cluster in gmm mode 

    '''
    def __init__(self, mus, sigmas, weight, label):
        self.n = 2 #number of dimensions 
        self.means = mus #mean values 
        self.stdevs = np.asarray(sigmas) #covarance matrix 
        self.weight = weight #weight of cluster
        self.label = label #label of cluster 
    def getPdf(self, p): #method to get weighted nd multivariate normal pdf 
        return multivariate_normal.pdf([p.x,p.y],self.means, self.stdevs, allow_singular=True) * self.weight

class GMM:
    '''
    GMM class - represents the GMM model 
    '''
    def __init__(self, dataset, k): #initialize parameters
        self.dataset = dataset #list of points
        self.resetDataset() #clear previous labels 
        self.dim = 2 # dimensions in dataset
        self.clusters = [] #list representing clusters
        mean_mat = [[random.randint(10,100)/100 for i in range(self.dim)] for kl in range(k)] # randomly initialize mean values for each cluster 
        stdev_mat = [[random.randint(10,100)/100 for i in range(self.dim)] for kl in range(k)] # randomly initialize covariance matrix for each cluster
        for i in range(k): # for each cluster
            stdev_mat_t = [[stdev_mat[i][0], 0], [0, stdev_mat[i][1]]] #reshape to be covariance matrix (initially assuming X, Y independent)
            self.clusters.append(GaussianCluster(mean_mat[i],stdev_mat_t, (1/k), i)) #add cluster to list
    def resetDataset(self): # helper function to reset dataset labels 
        for d in dataset:
            d.resetLabel()
    def expectationMax(self): #method to perform one round of expectation and maximization
        #mc_list - maintains list of # of points in a cluster, for max step
        mc_list = [0.001*len(self.dataset) for d in range(len(self.clusters))]
        ##EXPECTATION STEP 
        for i, p in enumerate(self.dataset): # for each point in dataset
            maxlabel = 0 # maintain cluster label that has maximum belongingless
            maxval = -1 # maintain maximum belongingness
            normalizer = sum([c.getPdf(p) for c in self.clusters]) #compute sum of pdfs of point in each cluster
            for j, c in enumerate(self.clusters): # for each cluster
                val = c.getPdf(p) / normalizer #compute belongingness to cluster
                if(val > maxval): # assign cluster label to point if point has higher belongingness to that cluster 
                    maxval = val
                    maxlabel = c.label
            mc_list[maxlabel] += 1 # increment # of points in the cluster with which point has highest belongingness
            p.label = maxlabel # assign point to that cluster 
        ##MAXIMIZATION STEP 
        res = [0 for i in self.clusters] #maintain list of results for each cluster 
        for j, c in enumerate(self.clusters): #for each cluster
            #recompute mean 
            mu = np.zeros((1, self.dim))
            for i, p in enumerate(self.dataset): # take sum of all points in dataset that belong to this cluster 
                mu = mu + (np.asarray([p.x, p.y]) * int(p.label == c.label))
            mu = ((1/mc_list[c.label]) * mu)[0] # normalize and reshape 
            #recompute covariance matrix 
            sig = np.zeros((self.dim, self.dim))
            for i, p in enumerate(self.dataset): # for all points in dataset
                diff_ximu = np.asarray([p.x, p.y]) - mu #compute vector p - mu where p is point (1x2 vector)
                prod = (np.reshape(diff_ximu, (self.dim, 1)) * diff_ximu) * int(p.label == c.label) # compute new 2x2 matrix for p 
                sig = np.add(sig, prod) # add that to covariance result 
            sig = (1/mc_list[c.label]) * sig #normalize covariance matrix 
            res[c.label] = (mu, sig) 
        return res 
    # method that performs expectation maximization on dataset repeatedly until change in parameters < eps
    def iterateToConverge(self, eps = 0.01, showall = False): 
        print("Error threshold set to", eps)
        iteration = 0 # maintain how many iterations passed 
        while(True):
            delta_mu = 0 #maintain sum of change in mu parameter
            delta_sig = 0 # maintain sum of change in sigma parameter
            iteration += 1
            print("At iteration #"+str(iteration))
            res = self.expectationMax() #run one iteration of expectation maximization
            for i, c in enumerate(self.clusters): #for each cluster 
                tmp = np.subtract(res[i][0], np.asarray(c.means)).tolist() #get difference between updated and old mean 
                delta_mu += sum([math.fabs(i) for i in tmp]) #take sum of absolute of all values in matrix 
                tmp = np.subtract(res[i][1], np.asarray(c.stdevs)).tolist() #get difference between updated and old covarance matrix 
                delta_sig += sum([sum([math.fabs(i) for i in t]) for t in tmp]) #take sum of absolute of all values in the matirx 
                self.clusters[i].means = res[i][0] #assign cluster new mean 
                self.clusters[i].stdevs = res[i][1] #assign cluster new covariance 
                print("\tCLUSTER", c.label)
                print("\t\tmean: ", res[i][0])
            if(showall == True): # show each iteration if parameter set 
                self.showResult(iteration = iteration)
            if(delta_mu < eps and delta_sig < eps): # if change in mu and sigma below threshold then stop 
                break
    def getCmap(self): #Helper function to map a color to each cluster (for visualization )
        N = len(self.clusters)
        color_norm  = colors.Normalize(vmin=0, vmax=N-1)
        scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='nipy_spectral') 
        def map_index_to_rgb_color(index):
            return scalar_map.to_rgba(index)
        return map_index_to_rgb_color
    def showResult(self, title = None, iteration = -1): #plot clustered dataset 
        if(title is None):
            title = "EMGMM RESULT"
        if(self.round != None):
            title += " Round #" + str(self.round) + " "
        if(iteration != -1):
            title += " Iteration #" + str(iteration)
        plt.title(title) #give plot title 
        cmap = self.getCmap() #get a mapping from cluster number to label
        for p in self.dataset:
            plt.scatter([p.x], [p.y], color=cmap(p.label)) #for each point plot it on graph with designated cluster's color
        plt.savefig(OUTDIR + title+".png", bbox_inches="tight") #save plot
        plt.clf()
        #plt.show()
             
dataset_o = scio.loadmat(FILENAME)["Points"]
def showOriginal(data): #METHOD TO SHOW THE ORIGINAL DATASET (WITH LABEL)
    def getCmap(): #same as class method GMM.getCmap()
        N = 2 #known fixed number of clusters 
        color_norm  = colors.Normalize(vmin=0, vmax=N-1)
        scalar_map = cmx.ScalarMappable(norm=color_norm, cmap='nipy_spectral') 
        def map_index_to_rgb_color(index):
            return scalar_map.to_rgba(index)
        return map_index_to_rgb_color
    def showResult(dataset): #same as class method GMM.showResult()
        cmap = getCmap()
        for p in dataset:
            plt.scatter([p[0]], [p[1]], color=cmap(int(p[2])))
        title = "Original dataset"
        plt.savefig(OUTDIR + title+".png", bbox_inches="tight") #save plot
        plt.clf()
        #plt.show()
    showResult(data)
showOriginal(dataset_o)
dataset = [Point(t[0], t[1]) for t in dataset_o] #convert to list of point objects
ROUNDS = 3
avg_acc = [] #maintain accuracy for each round
for i in range(ROUNDS): #for ROUNDS times 
    gmm = GMM(dataset, 2) #initialize GMM 
    gmm.round = i
    gmm.iterateToConverge(showall=True) #do expectation maximization until little change in parameters
    gmm.showResult() #show result
    acc = 0
    for i, d in enumerate(dataset): #for each point in dataset
        if d.label == dataset_o[i][2]: #if labels same then increment accuracy count 
            acc += 1
    avg_acc.append(max((acc / len(dataset)), 1-(acc / len(dataset)))) #take max of (acc, 1-acc) as clustering labels may have been flipped 

with open(OUTDIR + "accs.txt", "w+") as fw: #output accuracy stats to file
    for i, a in enumerate(avg_acc):
        fw.write("ITERATION "+str(i) + ": "+str(a) + "\n")
    fw.write("AVERAGE: "+str((sum(avg_acc) / len(avg_acc))) + "\n")
    
        
        
