from Expressions import *
#from RandomGraphGen import *
from GraphIO import *
from Simplifiers import *
from Evaluators import BaseEvaluator
from ViffEvaluator import ViffEvaluator

import sys

# Initialize Graph
ID = sys.argv[2]
ID = int(ID[ID.index("-")+1:ID.index(".")]) - 1
ID = str(ID)
nodes, edges_list, input_map = readGraph(open('mpc_graph/2MPC/input'+ID+'.txt', 'r').read())
edges_map = mapNodesToEdges(edges_list)

# Simplifiers
simplifier = MinToTopSimplifier()
simplifier2 = RemoveNestedAddSimplifier()
simplifier3 = RemoveRedundantMinSimplifier()

print "Initialized..."

# Initial "Symbolic" Values
value_map = {n: V(n) for n in nodes} # V -> FreeVarExp
for iteration in range(1): # """ len(nodes) """ Graph Distance Algorithm
    tmp = value_map
    for n in nodes:
        for nb, w in edges_map[n]:
            tmp[n] = min([tmp[n]] + [ value_map[nb] + w ]) # Simplify
            tmp[n] = tmp[n].simplify(simplifier).simplify(simplifier2).simplify(simplifier3)

    value_map = tmp

print "Algorithm Done..."

# Evaluate (Securely)
value_map = { n: (int(n[1:n.index("_")])+1, value_map[n]) for n in value_map }
value_map = ViffEvaluator.evaluate(input_map, value_map)

print "Evaluated!!"
print ""
print ""

# Print the graph
printGraph(nodes, edges_list, value_map)
