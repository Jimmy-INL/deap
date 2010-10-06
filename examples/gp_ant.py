#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

"""
This example is from "John R. Koza. Genetic Programming: On the Programming 
of Computers by Natural Selection. MIT Press, Cambridge, MA, USA, 1992.".

The problem is called The Artificial Ant Problem. 
<http://www.cs.ucl.ac.uk/staff/w.langdon/bloat_csrp-97-29/node2.html>

The goal of this example is to show how to use EAP and its GP framework with
with complex system of functions and object. 

Given an AntSimulator ant, this solution should get the 89 pieces of food
within 543 moves.
ant.routine = ant.if_food_ahead(ant.move_forward, prog3(ant.turn_left, 
                                                  prog2(ant.if_food_ahead(ant.move_forward, ant.turn_right), 
                                                        prog2(ant.turn_right, prog2(ant.turn_left, ant.turn_right))),
                                                  prog2(ant.if_food_ahead(ant.move_forward, ant.turn_left), ant.move_forward)))

Best solution found with EAP:
prog3(prog3(move_forward, 
            turn_right, 
            if_food_ahead(if_food_ahead(prog3(move_forward,
                                              move_forward, 
                                              move_forward), 
                                        prog2(turn_left, 
                                              turn_right)), 
                          turn_left)), 
      if_food_ahead(turn_left, 
                    turn_left), 
      if_food_ahead(move_forward, 
                    turn_right)) 
fitness = (89,)
"""

import sys
import logging
import copy
import random

from functools import partial

sys.path.append("..")

from eap import base
from eap import creator
from eap import toolbox
from eap import gp
from eap import algorithms
from eap import halloffame

logging.basicConfig(level=logging.DEBUG)

def progn(*args):
    for arg in args:
        arg()

def prog2(out1, out2): 
    return partial(progn,out1,out2)

def prog3(out1, out2, out3):     
    return partial(progn,out1,out2,out3)  

def if_then_else(condition, out1, out2):
    out1() if condition() else out2()

class AntSimulator(object):
    direction = ["north","east","south","west"]
    dir_row = [1, 0, -1, 0]
    dir_col = [0, 1, 0, -1]
    
    def __init__(self, max_moves):
        self.max_moves = max_moves
        self.moves = 0
        self.eaten = 0
        self.routine = None
        
    def _reset(self):
        self.row = self.row_start 
        self.col = self.col_start 
        self.dir = 1
        self.moves = 0  
        self.eaten = 0
        self.matrix_exc = copy.deepcopy(self.matrix)

    @property
    def position(self):
        return (self.row, self.col, self.direction[self.dir])
            
    def turn_left(self): 
        if self.moves < self.max_moves:
            self.moves += 1
            self.dir = (self.dir - 1) % 4

    def turn_right(self):
        if self.moves < self.max_moves:
            self.moves += 1    
            self.dir = (self.dir + 1) % 4
        
    def move_forward(self):
        if self.moves < self.max_moves:
            self.moves += 1
            self.row = (self.row + self.dir_row[self.dir]) % self.matrix_row
            self.col = (self.col + self.dir_col[self.dir]) % self.matrix_col
            if self.matrix_exc[self.row][self.col] == "food":
                self.eaten += 1
            self.matrix_exc[self.row][self.col] = "passed"

    def sense_food(self):
        ahead_row = (self.row + self.dir_row[self.dir]) % self.matrix_row
        ahead_col = (self.col + self.dir_col[self.dir]) % self.matrix_col        
        return self.matrix_exc[ahead_row][ahead_col] == "food"
   
    def if_food_ahead(self, out1, out2):
        return partial(if_then_else, self.sense_food, out1, out2)
   
    def run(self,routine):
        self._reset()
        while self.moves < self.max_moves:
            routine()
    
    def parse_matrix(self, matrix):
        self.matrix = list()
        for i, line in enumerate(matrix):
            self.matrix.append(list())
            for j, col in enumerate(line):
                if col == "#":
                    self.matrix[-1].append("food")
                elif col == ".":
                    self.matrix[-1].append("empty")
                elif col == "S":
                    self.matrix[-1].append("empty")
                    self.row_start = self.row = i
                    self.col_start = self.col = j
                    self.dir = 1
        self.matrix_row = len(self.matrix)
        self.matrix_col = len(self.matrix[0])
        self.matrix_exc = copy.deepcopy(self.matrix)

ant = AntSimulator(600)

pset = gp.PrimitiveSet("MAIN", 0)
pset.addPrimitive(ant.if_food_ahead, 2)
pset.addPrimitive(prog2, 2)
pset.addPrimitive(prog3, 3)
pset.addTerminal(ant.move_forward)
pset.addTerminal(ant.turn_left)
pset.addTerminal(ant.turn_right)

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("expr_init", gp.generateFull, pset=pset, min_=1, max_=2)

# Structure initializers
tools.register("individual", creator.Individual, content_init=tools.expr_init)
tools.register("population", list, content_init=tools.individual, size_init=300)

def evalArtificialAnt(individual):
    # Transform the tree expression to functionnal Python code
    routine = gp.evaluate(individual, pset)
    # Run the generated routine
    ant.run(routine)
    return ant.eaten,

tools.register("evaluate", evalArtificialAnt)
tools.register("select", toolbox.selTournament, tournsize=7)
tools.register("mate", toolbox.cxTreeUniformOnePoint)
tools.register("expr_mut", gp.generateFull, min_=0, max_=2)
tools.register("mutate", toolbox.mutTreeUniform, expr=tools.expr_mut)

if __name__ == "__main__":
    random.seed(101)

    trail_file = open("santafe_trail.txt")
    ant.parse_matrix(trail_file)
    
    pop = tools.population()
    hof = halloffame.HallOfFame(1)
    
    algorithms.eaSimple(tools, pop, 0.5, 0.2, 40, halloffame=hof)
    
    logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)
