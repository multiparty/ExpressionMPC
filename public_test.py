from Expressions import *
from RandomGraphGen import *
from GraphIO import *
from Simplifiers import AgressiveRedundantMinSimplifier
from Evaluators import BaseEvaluator

import sys

time_ = time()

# Read the graph
with open(sys.argv[1], 'r') as f:
    nodes, edges_list, input_map = readGraphs(f.read())[0]
edges_map = mapNodesToEdges(edges_list)

"""
# Random Graph
nodes, edges_list = genGraph(6, 6, 10, 11, 3)
edges_list = genWeights(edges_list)
edges_map = mapNodesToEdges(edges_list)
input_map = genValues(nodes) # Actual Input Values
"""

# Simplifiers
simplifier = AgressiveRedundantMinSimplifier()
AddExp.simpleAddLam = RemoveNestedAddSimplifier().simplifyAddExp

time2 = time()
print "Initialized... " + str(time2 - time_)

# Initial "Symbolic" Values
time1 = time()
value_map = {n: min([V(n)]) for n in nodes} # V -> FreeVarExp
for iteration in range(len(nodes)): # """ len(nodes) """ Graph Distance Algorithm
    tmp = {}
    for n in nodes:
        n_expression = value_map[n].operands
        for nb, w in edges_map[n]:
            n_expression = n_expression + [ o + w for o in value_map[nb].operands ]

        tmp[n] = min(n_expression)

    value_map = tmp
    value_map = {n: simplifier.simplifyMinExp(value_map[n], value_map[n].operands) for n in value_map }

time2 = time()
print "Algorithm Done... " + str(time2 - time1)

# Evaluate (Publicly)
time1 = time()
evaluator = BaseEvaluator(input_map)
value_map = {n : value_map[n].evaluate(evaluator) for n in value_map}

time2 = time()
print "Evaluated!! " + str(time2 - time1)
print "TOTAL TIME: " + str(time2 - time_)
print ""
print ""

# Print the graph
printGraph(nodes, edges_list, value_map)

