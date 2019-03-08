# -*- coding: utf-8 -*-
"""
This works.
pattern1StrideCsvOutput
@author: leoes
"""

import csv

from mesa import Agent, Model
#from mesa.time import RandomActivation
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
from math import *
import numpy as np
import random

# =============================================================================
# with open('reportRandomStride.csv', 'a') as reportFile:
#     rewriter = csv.writer(reportFile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#     rewriter.writerow(['Step', 'InteractionRate', "AverageInteractionRate", 'Area', "CoveragePercentage", "AveragePercentage"]) 
#     
# =============================================================================

def compute_coverage(model):
    model.coveredArea = []
    edgeOffset = 0
    for agent in model.schedule.agents:
        x, y = agent.pos
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                model.coveredArea.append((x+dx, y+dy))
                if x+dx < 0 or x+dx > model.width or y+dy < 0 or y+dy > model.height:
                    edgeOffset += 1
    
# =============================================================================
#     if model.schedule.steps > 5:
#         for i in range(model.N*9):
#             model.coveredArea.pop(i)
#     
#     for i in range(0,len(model.coveredArea)):
#         if model.coveredArea[i][0] < 0 or model.coveredArea[i][0] > model.width or model.coveredArea[i][1] < 0 or model.coveredArea[i][1] > model.height:
#             edgeOffset += 1
# =============================================================================
                    
    coverIndex = len(set(model.coveredArea)) - edgeOffset
    print("coverIndex", coverIndex)
    
    return coverIndex


class MoniModel(Model):
    """A simple model of an economy where agents exchange currency at random.

    All the agents begin with one unit of currency, and each time step can give
    a unit of currency to another agent. Note how, over time, this produces a
    highly skewed distribution of wealth.
    """

    def __init__(self, N, width, height):
        self.num_agents = N
        self.width = width
        self.height = height
        self.grid = MultiGrid(height, width, False) #non toroidal grid
        self.schedule = SimultaneousActivation(self)
        self.datacollector = DataCollector(
            model_reporters={"Coverage": compute_coverage},
            agent_reporters={"Wealth": "wealth"}
        )
        # Create agents
        self.coveredArea = []
        self.interactionCount = 0
        self.interactionRateAverage = 0
        self.coveragePercentage = 0
        self.coveragePercentageAverage = 0
        
#        distribute the agents evently
        areaNum = ceil(sqrt(self.num_agents))
        areaDistx = self.width/(sqrt(self.num_agents))
        areaDistx = floor(areaDistx)
        areaDisty = self.height/(sqrt(self.num_agents))
        areaDisty = floor(areaDisty)
        
        self.dtx = areaDistx
        self.dty = areaDisty
        
        for i in range(self.num_agents):
            
            xlow = (i%areaNum)*areaDistx
            xup = xlow + areaDistx-1
            
            ylow = floor(i/areaNum)*areaDisty
            yup = ylow + areaDisty-1
        
            x = floor((xlow+xup)/2)+1
            y = floor((ylow+yup)/2)+1
            
           
            
            
            xlow = x-1
            xup = x+1
            ylow = y-1
            yup = y+1
            
#            create and add agent with id number i to the scheduler
            a = MoniAgent(i, self, xup, xlow, yup, ylow)
            self.schedule.add(a)
            
            #place agent at the center of its limit coor
            self.grid.place_agent(a, (x, y))
            # Add the agent to a random grid cell
            
#        this part is for visualization only
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.interactionCount = 0
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        
       
        
        with open('reportRandomStride.csv', 'a') as reportFile:
            coverage = compute_coverage(self)
            percentage = ceil(10000*coverage/self.width/self.height)/100 
            
            interactionRate = self.interactionCount/self.num_agents/(self.num_agents-1)
            #number of interaction/possible interaction /2 for double counting
            interactionRate = ceil(10000*interactionRate)/100
            
            self.interactionRateAverage = (self.interactionRateAverage*(self.schedule.steps-1) + interactionRate)/self.schedule.steps
            self.interactionRateAverage  = ceil(100*self.interactionRateAverage)/100
            
            self.coveragePercentageAverage = (self.coveragePercentageAverage*(self.schedule.steps-1)+percentage)/self.schedule.steps
            self.coveragePercentageAverage = ceil(100*self.coveragePercentageAverage)/100
            
            rewriter = csv.writer(reportFile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            rewriter.writerow(["step:", self.schedule.steps, "InteractionRate:", interactionRate,'%', "AvgInteractionRate", self.interactionRateAverage,'%', "Coverage:", coverage, percentage,'%',self.coveragePercentageAverage,'%'])

#    def initPosTest(self)
    
   
    
    def run_model(self, n):
        for i in range(n):
#            self.initPos()
            self.step()
#            print(self.schedule.steps)
    
class MoniAgent(Agent):
    def __init__(self, unique_id, model, xup, xlow, yup, ylow):
#        , prevPos = (0,0)
        super().__init__(unique_id, model)
        self.xup = xup
        self.xlow = xlow
        self.yup = yup
        self.ylow = ylow
        self.wealth = 1
        self.returnFlag = False
        self.origin = ((xup-1),(yup-1)) #starting point
        self.forcex = 0
        self.forcey = 0
        self.nextPos = (0,0) 
		#new pos that will be move to in self.advance
		
        self.freeStep = 0 
        #number of steps with no close contact with other agents
        
        self.reflectX = True
        #plane of reflection parallel to x axis
        
        self.stepx = 0
        self.stepy = 0 
        #step in x and y direction of the last move
        

#    used for spiral movement
    def resetSpaceLim(self):
        self.xup = self.pos[0]+1
        self.xlow = self.pos[0]-1
        self.yup = self.pos[1]+1
        self.ylow = self.pos[1]-1
        
        
    def confrontOther(self):
#        return true if an agent is close to another agent (Manhattan distance < 3)
        for agent in self.model.schedule.agents:
            if self != agent:
                if abs(self.pos[0]-agent.pos[0]) < 3 and abs(self.pos[1]-agent.pos[1]) < 3:
                    self.model.interactionCount += 1
                    oldAgentPos = (agent.pos[0]-agent.stepx, agent.pos[1]-agent.stepy)
                    tx = self.pos[0]-oldAgentPos[0]
                    ty = self.pos[1]-oldAgentPos[1]
                    
                    if tx != 0:
                        tx = self.pos[0] + int(tx/abs(tx))
                    else:
                            tx = self.pos[0]
                    if ty != 0:
                        ty = self.pos[1] + int(ty/abs(ty))
                    else:
                            ty = self.pos[1]
                    
                    self.origin = (tx,ty)
                    
                    while self.model.grid.out_of_bounds(self.origin):
                        self.stepx = random.randrange(3)-1
                        self.stepy = random.randrange(3)-1
                        self.origin = (self.pos[0]+self.stepx,self.pos[1]+self.stepy)
                    
# =============================================================================
#                     print("pos and origin")
#                     print(self.pos)
#                     print(self.origin)
#                     
#                     print("origin")
#                     print(self.origin)
# ================================================ =============================
                    
                    return True 
            
# =============================================================================
#             if self.pos[1] < 2 or (self.model.height - self.pos[1]) < 2:
#                 self.reflectX = True
#                 return True
#             if self.pos[0] < 2 or (self.model.width - self.pos[0]) < 2:
#                 self.reflectX = False
#                 return True
# =============================================================================
            
        return False

        
# =============================================================================
#     def move(self):
# #        it is supposed that initially agents are not close to others when this method is called, that means returnFlag is False
#         if self.returnFlag == False: 
#             if self.confrontOther() == False:
#                 possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
#                 self.nextPos = self.random.choice(possible_steps)
#             else: #confront others
#                 self.returnFlag == True
#                 xx = random.randrange(self.model.grid.width)
#                 yy = random.randrange(self.model.grid.height)
#                 self.origin = (xx,yy) #the new position for the agents to move to
#                 
#         if self.returnFlag == True:
#             xx, yy = self.origin 
#             x, y = self.pos
#             if self.pos != self.origin:
#                 if x != xx:
#                     x += (xx-x)//abs(xx-x) #move to an diagonally adjacent cell
#                 if y != yy:
#                     y += (yy-y)//abs(yy-y)
# #               print("I have returned ")
#                 if self.pos == self.origin: #agent has finished it stride, it is not returning anymore
#                     self.returnFlag = False  
#                     self.wealth = 1
#             
#             self.nextPos = (x,y)
# =============================================================================
        
    
    def returnn(self):     
        x, y = self.pos
        xx, yy = self.origin   
        if x != xx:
            x += (xx-x)//abs(xx-x) #move to an adjacent cell
        if y != yy:
            y += (yy-y)//abs(yy-y)
        self.nextPos = (x,y)
        if self.nextPos == self.origin:
            self.returnFlag = False
            self.wealth = 1
        
    def move(self):
        def new_pos():
#            xp, yp = self.prevPos
            x, y = self.pos
            #return original point if out of bounds
            if self.confrontOther():
                self.returnFlag = True
                self.wealth = 0
# =============================================================================
#                 print("want to change origin", self.origin)
#                 ax = random.randrange(self.model.grid.width)
#                 #self.random... does not work
#                 ay = random.randrange(self.model.grid.height)
# #                self.origin = (ax,ay)
#                 print("ax", ax)
# =============================================================================

                return self.pos
            else:
                self.freeStep += 1
                while True:
                    self.stepx = random.randrange(3)-1
                    self.stepy = random.randrange(3)-1
                    new_pos = (self.pos[0]+self.stepx,self.pos[1]+self.stepy)
                    if not self.model.grid.out_of_bounds(new_pos):
                        break
                return new_pos
            
        self.nextPos = new_pos()


    def step(self):
        if self.returnFlag == False:
            self.move()
        else:
            self.returnn()
   
#    next step after staged change
    def advance(self):
        self.model.grid.move_agent(self, self.nextPos)
        


#visualization module =======================================================================
#============================================================================================
            
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter


def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5}

    if agent.wealth > 0:
        portrayal["Color"] = "green"
        portrayal["Layer"] = 0
    else:
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5
    return portrayal


grid = CanvasGrid(agent_portrayal, 100, 100, 512, 512)
chart1 = ChartModule([{"Label": "Coverage", "Color": "#0000FF"}], data_collector_name='datacollector')


    
model_params = {
    "N": UserSettableParameter('slider', "Number of agents", 16, 1, 200, 1,
                               description="Choose how many agents to include in the model"),
    "width": 100, 
    "height": 100
}

#server = ModularServer(MoniModel, [grid, chart], "Money Model", model_params)
server = ModularServer(MoniModel, [grid], "Monitoring pattern", model_params)
server.port = 8426
server.launch()