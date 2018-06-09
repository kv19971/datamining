#!usr/bin/python3 
import math
import pandas as pd
import numpy as np


FILENAME = "clickstreamevent.csv"

def readData(): #function to read data from csv
    data = pd.read_csv(FILENAME)
    return data.values

class Point: #Point class represents a 5d point 
    def __init__(self, data, dist_mode = 'E'):
        self.data = data[1:] # get all attribute values except user id 
        self.mode = dist_mode # mode to calculate distance 
        self.userid = str(data[0]) #set userid associated with that point 
        self.kthneighbor = None #Kth nearest neighbor
        self.knn_group = [] # list of points that are closer than the kth nearest point and the kth nearest point 
    def distance(self, p): #function to calculate distance between this point and point p
        if(self.mode == 'E'): #if euclidian then give euclidian distance 
            r = 0
            for i, d in enumerate(self.data):
                r += math.pow((d - p.data[i]), 2)
            return math.sqrt(r)
        else:  #else give manhattan distance 
            r = 0
            for i, d in enumerate(self.data):
                r += math.fabs(d - p.data[i])
            return r
    def reachDist(self, o, obar): 
        """reachDist as done in the paper, get the max of distance between obar and its kth neighbor 
        and distance between o and obar"""
        return max(obar.distance(obar.kthneighbor), o.distance(obar))
    def localReachDensity(self): #get density of the neighborhood of the current point
        sum_reachdist = 0
        for p in self.knn_group: #for each point in the k neighborhood
            sum_reachdist += self.reachDist(self, p) #add reachDist for that point 
        return len(self.knn_group) / sum_reachdist #return inverse of average reachDist
    def calculateLOF(self): #Calculate LOF for a point 
        sum_reachability = 0
        self_lrd = self.localReachDensity() #current point's local reachability density 
        for p in self.knn_group: #for each point in k neighborhood
            sum_reachability += p.localReachDensity() / self_lrd #calculate ratio between that point's local reachability density
            # and current point's local reachability density 
        return (sum_reachability) / (len(self.knn_group)) #return average of all ratios

class LOF: 
    """LOF class created for better organization - maintains list of all points and 
    populates their k nearest neighborhood"""
    def __init__(self, rawdata, k, dist_metric):
        self.points = []
        for r in rawdata: #add points to list
            self.points.append(Point(r, dist_metric))
        self.dist_metric = dist_metric # set distance metric
        self.k = k # set k
    def populateKnn(self, pointIndex): #function to get all points in kth neighborhood of a point (referenced by index of point, pointIndex)
        ref_point = self.points[pointIndex] #current point
        relative_ref = self.points 
        relative_ref = sorted(relative_ref, key=lambda p1: ref_point.distance(p1)) #sort all points by distance to current point
        relative_ref = [r for r in relative_ref if r.userid != self.points[pointIndex].userid] #remove current point from that list 
        self.points[pointIndex].knn_group = relative_ref[:self.k] #get the k closest points 
        prevdist = relative_ref[self.k].distance(ref_point) #get the distance to kth closest point 
        #loop to handle cases where there may be points having distance to current point that is same as distance between current point
        # and kth closest point
        for i in range(self.k+1, len(relative_ref)): #for every point after kth point
            if math.isclose(relative_ref[i].distance(ref_point), prevdist) == True: #if it is same as distance to kth point
                self.points[pointIndex].knn_group.append(relative_ref[i]) #then add it to the list 
            else: #otherwise stop
                break
        self.points[pointIndex].kthneighbor = self.points[pointIndex].knn_group[-1] #set kth nearest point 
    def getAllLOF(self, n=5): #function to get all points with lof score
        lof_list = [] #maintain list of tuples with user id and lof score
        for i, p in enumerate(self.points): #get kth neighborhood for all points 
            self.populateKnn(i)
        for i, p in enumerate(self.points): #for each point calculate lof score
            lof_list.append((p.userid, p.calculateLOF())) 
        lof_list.sort(key=lambda x: x[1], reverse=True) #sort in descending order by lof score 
        return lof_list[:n] #get the top n outliers




data = [['a',0,0,1,4,5],
        ['b',0,1,1,4,5],
        ['c',1,1,1,4,5],
        ['d',3,0,1,4,5]
    ]
lof = LOF(data, 2, 'M')
print("SANITY CHECK - EXAMPLE STOLEN FROM LECTURE SLIDES")
results = lof.getAllLOF()
print(results)
print("ACTUAL DATA FROM CSV")
data = readData() #read data from csv
params = [(2, 'M'), (3, 'M'), (2, 'E'), (3, 'E')] #different params to run lof on
for p in params:
    #for each param get top 5 outliers and their scores
    print("FOR k="+str(p[0])+" and distance metric="+p[1]) 
    lof = LOF(data, p[0], p[1])
    results = lof.getAllLOF()
    for r in results:
        print(r[0] + ": " + str(r[1]))
    print("")
            