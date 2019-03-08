# -*- coding: utf-8 -*-
"""
Created on Sun Feb  3 03:41:38 2019

@author: leoes
"""
import pattern2TotalRandomCsvOutput
import pattern1StrideCsvOutput

# =============================================================================
# f = open("reportRandomStride.csv", "w")
# f.truncate()
# f.close()
# 
# f = open('reportRandomStride.csv', "w")
# f.truncate()
# f.close()
# =============================================================================

model = BoltzmannWealthModel(100,1000,1000)
model.run_model(2000)

model = RandomMoveModel(100,1000,1000)
model.run_model(2000)