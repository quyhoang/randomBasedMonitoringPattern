# -*- coding: utf-8 -*-
"""
Created on Sun Feb  3 03:28:06 2019
pattern2TotalRandomCsvOutput
@author: leoes
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Feb  3 01:53:43 2019

@author: leoes
"""

import csv

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from math import *
import numpy as np
import random

with open('reportRandom.csv', 'a') as reportFile:
    rewriter = csv.writer(reportFile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    rewriter.writerow(['Step', 'InteractionRate', "AverageInteractionRate", 'Area', "CoveragePercentage", "AveragePercentage"]) 
    
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
#    print("coverIndex", coverIndex)
    
    return coverIndex


class RandomMoveModel(Model):
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
        self.schedule = RandomActivation(self)
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
            
            a = MoneyAgent(i, self, xup, xlow, yup, ylow)
            self.schedule.add(a)
            
            #place agent at the center of its limit coor
            self.grid.place_agent(a, (x, y))
            # Add the agent to a random grid cell
            

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        print(self.schedule.steps)
        self.interactionCount = 0
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        
       
        
        with open('reportRandom.csv', 'a') as reportFile:
            coverage = compute_coverage(self)
            percentage = ceil(10000*coverage/self.width/self.height)/100 
            
            interactionRate = self.interactionCount/self.num_agents/(self.num_agents-1) #number of interaction/possible interaction /2 for double counting
            interactionRate = floor(10000*interactionRate)/100
            
            self.interactionRateAverage = (self.interactionRateAverage*(self.schedule.steps-1) + interactionRate)/self.schedule.steps
            self.interactionRateAverage  = ceil(100*self.interactionRateAverage)/100
            
            self.coveragePercentageAverage = (self.coveragePercentageAverage*(self.schedule.steps-1)+percentage)/self.schedule.steps
            self.coveragePercentageAverage = ceil(100*self.coveragePercentageAverage)/100
            
            rewriter = csv.writer(reportFile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            rewriter.writerow(["step:", self.schedule.steps, "InteractionRate:", self.interactionCount, interactionRate,'%', "AvgInteractionRate", self.interactionRateAverage,'%', "Coverage:", coverage, percentage,'%',self.coveragePercentageAverage,'%'])

    def run_model(self, n):
        for i in range(n):
            self.step()
#            print(self.schedule.steps)
    
    def initPos(self):
        for agent in self.schedule.agent_buffer():
            for i in self.schedule.agent_buffer():
                if i!= agent:
#                    print ("Heldddlo")
#                    divisor = ((i.pos[0]-agent.pos[0])**2+(i.pos[1]-agent.pos[1])**2)
                    divisor = ((i.pos[0]-agent.pos[0])+(i.pos[1]-agent.pos[1]))
                    agent.forcex += (agent.pos[0]-i.pos[0])/divisor
                    agent.forcey += (agent.pos[1]-i.pos[1])/divisor
                    
            #virtual force from boundary
            lx = self.dtx/2 - agent.pos[0]
            ly = self.dty/2 - agent.pos[1]
            ux = self.dtx/2 - (self.width - agent.pos[0])
            uy = self.dty/2 - (self.height - agent.pos[1])
# =============================================================================
#             agent.forcex += (np.heaviside(lx,0)/(lx**2) - np.heaviside(ux,0)/(ux**2))
#         
#             agent.forcey += (np.heaviside(ly,0)/(ly**2) - np.heaviside(uy,0)/(uy**2))
# =============================================================================
            
            agent.forcex += (np.heaviside(lx,0)/(lx) - np.heaviside(ux,0)/(ux))
        
            agent.forcey += (np.heaviside(ly,0)/(ly) - np.heaviside(uy,0)/(uy))
        for agent in self.model.schedule.agent_buffer(): 
            vx = agent.forcex/np.linalg.norm(agent.force)
            vy = agent.forcey/np.linalg.norm(agent.force)
            
            apx = agent.pos[0]
            apy = agent.pos[1]
            if abs(vx) > 0.5:
                apx += vx//abs(vx)
            if abs(vy) > 0.5:
                apy += vy//abs(vy)
            self.grid.place_agent(agent, (apx, apy))
            
    
class MoneyAgent(Agent):
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
# =============================================================================
#     def distToOther(self, *pos):
#         return abs(self.pos[0]-pos[0])+abs(self.pos[1]-pos[1])
#         # manhattan distance
        
#        THIS CAUSES A SERIOUS BUG. HOW TO PASS TUPLE AS ARGUMENT PROPERLY?
# =============================================================================
    def resetSpaceLim(self):
        self.xup = self.pos[0]+1
        self.xlow = self.pos[0]-1
        self.yup = self.pos[1]+1
        self.ylow = self.pos[1]-1
        
        
    def confrontOther(self):
#        for agent in self.model.schedule.agent_buffer():
        for agent in self.model.schedule.agents:
            if self != agent:
                if abs(self.pos[0]-agent.pos[0])+abs(self.pos[1]-agent.pos[1]) < 3:
                    self.model.interactionCount += 1
                    return True
                
        return False



    def returnn(self):
#        print("returning")
        x, y = self.pos

        xx, yy = self.origin
#        print("selfpos") 
        print(self.pos)
#        print("selforg")
#        print(self.origin)
        if self.pos == self.origin:
            self.returnFlag = False
            self.wealth = 1
            self.xlow = x-1
            self.xup = x+1
            self.ylow = y-1
            self.yup = y+1
        else:
            if x != xx:
                x += (xx-x)//abs(xx-x) #move to an adjacent cell
            if y != yy:
                y += (yy-y)//abs(yy-y)
#            print("I have returned ")
#            print((x,y))
            
            self.model.grid.move_agent(self, (x,y))
        
    def move(self):
        def new_pos():
#            xp, yp = self.prevPos
            x, y = self.pos
            #return original point if out of bounds
            if self.confrontOther():
                self.returnFlag = True
                self.wealth = 0
#                print("want to change origin", self.origin)
                ax = random.randrange(self.model.grid.width)
                #self.random... does not work
                ay = random.randrange(self.model.grid.height)
                self.origin = (ax,ay)
#                print("ax", ax)

                return self.pos
            else:
                possible_steps = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False)
                return self.random.choice(possible_steps)
        
            
        self.model.grid.move_agent(self, new_pos())
#        print(self.pos)

    def step(self):
        self.move()
    
# =============================================================================
#     def step(self):
#         print(self.model.schedule.steps)
# # =============================================================================
# #         if self.model.schedule.steps%1000 < 100:
# #             print(self.model.schedule.steps%50)
# #             self.model.initPos()
# #             print("Is it working?")
# #             self.model.schedule.steps += 1
# # =============================================================================
#             
#         if self.returnFlag == False:
#             self.move()
#         else:
#             self.returnn()
#             print(self.returnFlag)
# =============================================================================
        
        
        
        

# =============================================================================
# 
# #visualization module =======================================================================
# #============================================================================================
#             
# from mesa.visualization.ModularVisualization import ModularServer
# from mesa.visualization.modules import CanvasGrid
# from mesa.visualization.modules import ChartModule
# from mesa.visualization.UserParam import UserSettableParameter
# 
# 
# def agent_portrayal(agent):
#     portrayal = {"Shape": "circle",
#                  "Filled": "true",
#                  "r": 0.5}
# 
#     if agent.wealth > 0:
#         portrayal["Color"] = "green"
#         portrayal["Layer"] = 0
#     else:
#         portrayal["Color"] = "red"
#         portrayal["Layer"] = 1
#         portrayal["r"] = 0.5
#     return portrayal
# 
# 
# grid = CanvasGrid(agent_portrayal, 100, 100, 512, 512)
# chart1 = ChartModule([
#     {"Label": "Coverage", "Color": "#0000FF"}],
#     data_collector_name='datacollector'
# )
# 
# # =============================================================================
# # chart2 = ChartModule([
# #     {"Label": "Coverage", "Color": "#0000F0"}],
# #     data_collector_name='datacollector'
# # )
# # =============================================================================
#     
# model_params = {
#     "N": UserSettableParameter('slider', "Number of agents", 25, 1, 200, 4,
#                                description="Choose how many agents to include in the model"),
#     "width": 100, 
#     "height": 100
# }
# 
# #server = ModularServer(BoltzmannWealthModel, [grid, chart], "Money Model", model_params)
# server = ModularServer(BoltzmannWealthModel, [grid, chart1], "Monitoring pattern", model_params)
# server.port = 8426
# server.launch()
# 
# =============================================================================
