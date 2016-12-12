from Expressions import *
from RandomGraphGen import *
from GraphIO import *
from Simplifiers import *
from Evaluators import BaseEvaluator
from ViffEvaluator import ViffEvaluator

from time import clock as time
import sys

# Initialize Graph
time_ = time()

ID = sys.argv[2]
ID = int(ID[ID.index("-")+1:ID.index(".")]) - 1
ID = str(ID)
nodes, edges_list, input_map = readGraph(open('mpc_graph/2MPC/input'+ID+'.txt', 'r').read())
edges_map = mapNodesToEdges(edges_list)

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

# Evaluate (Securely)
time1 = time()
value_map = { n: (int(n[1:n.index("_")])+1, value_map[n]) for n in value_map }
value_map = ViffEvaluator.evaluate(input_map, value_map)

time2 = time()
print "Evaluated!! " + str(time2 - time1)
print "TOTAL TIME: " + str(time2 - time_)
print ""
print ""

# Print the graph
printGraph(nodes, edges_list, value_map)
