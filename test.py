from Expressions import *
from RandomGraphGen import *
from GraphIO import *
from Simplifiers import MinToTopSimplifier, RemoveNestedAddSimplifier, RemoveRedundantMinSimplifier
from Evaluators import BaseEvaluator

import sys

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
simplifier = MinToTopSimplifier()
simplifier2 = RemoveNestedAddSimplifier()
simplifier3 = RemoveRedundantMinSimplifier()

print "Initialized..."

# Initial "Symbolic" Values
value_map = {n: V(n) for n in nodes} # V -> FreeVarExp
for iteration in range(len(nodes)): # Graph Distance Algorithm
    tmp = value_map
    for n in nodes:
        for nb, w in edges_map[n]:
            tmp[n] = min([tmp[n]] + [ value_map[nb] + w ]) # Simplify
            tmp[n] = tmp[n].simplify(simplifier).simplify(simplifier2).simplify(simplifier3)

    value_map = tmp

print ""
print ""
for key in value_map:
    print key, ": ", value_map[key]

print "Algorithm Done..."

# Evaluate (Publicly)
evaluator = BaseEvaluator(input_map)
value_map = {n : value_map[n].evaluate(evaluator) for n in value_map}

print "Evaluated!!"
print ""
print ""

"""
# Print the graph
graphs = [(nodes, edges_list, input_map), (nodes, edges_list, value_map)]
printGraphs(graphs)
"""

# Print the graph
printGraph(nodes, edges_list, value_map)
