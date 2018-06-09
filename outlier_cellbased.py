#!usr/bin/python3 
import math
import pandas as pd
import matplotlib.pyplot as plt

OUTDIR = "cell_outs/"
FILENAME = "clickstreamevent.csv"

def readData(relevantAttributes): #read data from csv but only the given attributes + user id 
    data = pd.read_csv(FILENAME)
    data = data[["user_id"] + relevantAttributes]
    return data.values

class Point: 
    """class to represent point object """
    def __init__(self, data):
        self.data = data[1:] 
        self.user_id = data[0] #1-1 mapping b/w user id and point
        self.outlier = False #non outlier by default 
    def markAsOutlier(self): #helper function to set as outlier
        self.outlier = True
    def distance(self, p): #get euclidian distance between current point and point p 
        r = 0
        for i, d in enumerate(self.data):
            r += math.pow((d - p.data[i]), 2)
        return math.sqrt(r)

class Cell:
    """Class to represent cell object - holds list of points in the cell"""
    def __init__(self):
        #self.range = range #range that cell covers on the grid (for reference only )
        self.points = [] #list of points in the cell
        self.color = "WHITE" #default color (white == uncolored ) 
    def addPointToCell(self, point): #add point to cell
        self.points.append(point)
    def getNumPoints(self): # get number of points in cell
        return len(self.points)

class Grid:
    """Class to represent grid of cells """
    def __init__(self, data, r, m):
        self.r = r #parameter d, where d/2 is diagonal length of each cell
        self.m = m #points threshold
        self.x_min, self.x_max = min(data.T[1]), max(data.T[1]) #x bounds of the grid 
        self.y_min, self.y_max = min(data.T[2]), max(data.T[2]) #y bounds of the grid 
        self.grid = []
        self.assembleGrid() #add appropriate number of cells to grid 
        for d in data: #for each datapoint assign it to a cell in the grid 
            self.addPointToGrid(Point(d))
    
    def assembleGrid(self): #function to add appropriate matrix of cells to grid 
        block_size = self.r/(2*math.sqrt(2)) #get block height and width
        num_x = math.ceil((self.x_max - self.x_min) / block_size) #number of cols 
        num_y = math.ceil((self.y_max - self.y_min) / block_size) #num of rows 
        for i in range(num_y): #for each row 
            self.grid.append([]) # add empty row 
            for j in range(num_x): #for each col
                self.grid[i].append(Cell()) # add empty cell in current row 

    def addPointToGrid(self, point): #function to add point to appropriate cell in grid 
        block_size = self.r/(2*math.sqrt(2)) #block height/width 
        block_x = math.floor((point.data[0] - self.x_min) / (block_size)) #column of block - based on x coordinate of point  
        block_y = math.floor((point.data[1] - self.y_min) / (block_size)) #row of block - based on y coordinate of point 
        if((block_x > (len(self.grid[0]) - 1) ) or (block_y > (len(self.grid) - 1))): #sanity check 
            raise ValueError("Invalid point given. Please give a point within range")
        self.grid[block_y][block_x].addPointToCell(point) #add point to that cell 
    
    def getL2List(self, cell): #function to get L2 neighbors of a cell 
        lst = []
        l1lst = self.getL1List(cell) #get L1 neighbors first
        r_bounds = (max(cell[0]-3, 0), min(cell[0]+4, len(self.grid))) #row range of L2 neighbors 
        c_bounds = (max(cell[1]-3, 0), min(cell[1]+4, len(self.grid[0]))) #col range of L2 neighbors 
        for i in range(r_bounds[0], r_bounds[1]): #iterate over rows and columns in L2 and add them to list 
            for j in range(c_bounds[0], c_bounds[1]):
                if (i == cell[0] and j==cell[1]) or ((i,j) in l1lst): #if cell is the current cell or L1 neighbor then skip it 
                    continue
                lst.append((i,j)) #else add to list
        return lst

    def getL1List(self, cell): #function to get l1 neighbors of a cell
        lst = []
        for i in range(max(cell[0]-1, 0), min(cell[0]+2, len(self.grid))): #for each row in l1 neighborhood
            for j in range(max(cell[1]-1, 0), min(cell[1]+2, len(self.grid[0]))): #for each col un l1 neighborhood
                if i == cell[0] and j==cell[1]: #if cell is current cell then skip 
                    continue
                lst.append((i,j)) #else add it to list 
        return lst
                
    def colorGrid(self): #function to "color" cells in grid and label points as outliers 
        #first color all densely populated cells red 
        redcells = set() #maintain list of red cells for later 
        for i, r in enumerate(self.grid):
            for j, c in enumerate(self.grid[i]):
                if c.getNumPoints() > self.m:
                    self.grid[i][j].color = "RED"
                    redcells.add((i, j))
        #then color all L1 neighbors of red cells pink, if they are not already labelled red 
        for r in redcells:
            l1cells = self.getL1List(r)
            for t in l1cells:
                if self.grid[t[0]][t[1]].color != "RED":
                    self.grid[t[0]][t[1]].color = "PINK"
        #for each cell in grid 
        for i, r in enumerate(self.grid):
            for j in range(len(self.grid[i])):
                if(self.grid[i][j].color != "WHITE"): #if cell colored then skip
                    continue
                #get count of points in cell and L1 neighborhood
                count_w2 = 0
                l1cells = self.getL1List((i,j))
                for c in l1cells:
                    count_w2 += self.grid[c[0]][c[1]].getNumPoints()
                if(count_w2 > self.m): #if it is greater than the m threshold then label it pink 
                    self.grid[i][j].color = "PINK"
                else:
                    #get count of points in cell L1 neighborhood and L2 neighborhood
                    count_w3 = count_w2 
                    l2cells = self.getL2List((i,j))
                    for c in l2cells:
                        count_w3 += self.grid[c[0]][c[1]].getNumPoints()
                    if count_w3 <= self.m: #if count less than threshold then mark all points in current cell as outliers 
                        for pi, p in enumerate(self.grid[i][j].points):
                            self.grid[i][j].points[pi].markAsOutlier()
                    else: #otherwise for each point in cell compare distance with points in L2 neighbors of cell
                        for pi, p in enumerate(self.grid[i][j].points):
                            count_p = 0
                            for c in l2cells:
                                for pc in (self.grid[c[0]][c[1]].points):
                                    if p.distance(pc) <= self.r: #if distance is less than threshold then add to count of point 
                                        count_p += 1
                            if count_p <= self.m: #if count is less than threshold then mark that point as outlier
                                self.grid[i][j].points[pi].markAsOutlier()


attr_combos = [["pause_video", "play_video"], ["play_video", "seek_video"]] #different attribute combos to be considerd
for attrs in attr_combos: #for each attr
    data = readData(attrs) #read data on current attrs 
    attr_string = attrs[0] + " and " + attrs[1] 
    dvals = [10,15,20,25] #different d values to be tested
    mvals = [5,10] # different m values to be tested
    #for each combo of d aand m
    for d in dvals: 
        for m in mvals:
            grid = Grid(data, d, m) #make grid with d = d and m = m
            grid.colorGrid() #"color" each cell in grid and mark points as outliers
            outliers = [] #maintain list of outliers
            #for each cell in grid
            for i in range(len(grid.grid)): 
                for c in grid.grid[i]:
                    #for each point in cell
                    for p in c.points:
                        #plot point on graph
                        plt.scatter(p.data[0], p.data[1], color=("black" if p.outlier == True else "red")) #different colors for outliers
                        if p.outlier == True:
                            outliers.append(p.user_id)
            title = attr_string + " D="+str(d) + " M="+str(m) + " : We have " + str(len(outliers)) + "outliers "
            plt.title(title) #plot points
            plt.savefig(OUTDIR + title+".png", bbox_inches="tight")
            plt.clf()

