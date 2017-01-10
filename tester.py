from Expressions import *
from RandomGraphGen import *
from GraphIO import *
from Simplifiers import *
from Evaluators import BaseEvaluator

from time import clock as time
import sys

def compare(e1, e2):
    if isinstance(e1, AtomicIntExp) and isinstance(e2, AtomicIntExp): return e1.value() - e2.value()
    if isinstance(e1, AtomicIntExp): return 1
    if isinstance(e2, AtomicIntExp): return -1

    e1, e2 = str(e1), str(e2)

    if ":" in e1 and not ":" in e2: return 1
    if not ":" in e1 and ":" in e2: return -1

    if e1 < e2: return -1
    if e1 == e2: return 0
    return 1


# Initialize Graph
time_ = time()

# Random Graph
nodes, edges_list = genGraph(5,5,5,5,5,2)
edges_list = genWeights(edges_list)
edges_map = mapNodesToEdgesWithWeights(edges_list, nodes)
input_map = genValues(nodes) # Actual Input Values
print nodes

# Simplifiers
simplifier = AgressiveRedundantMinSimplifier()
AddExp.simpleAddLam = RemoveNestedAddSimplifier().simplifyAddExp

time2 = time()
print "Initialized... " + str(time2 - time_)

# Initial "Symbolic" Values
time1 = time()
value_map = {n: min([V(n)]) for n in nodes} # V -> FreeVarExp
for iteration in range(2): # """ len(nodes) """ Graph Distance Algorithm
    tmp = {}
    for n in nodes:
        n_expression = value_map[n].operands
        for nb, w in edges_map[n]:
            print w
            n_expression = n_expression + [ o + w for o in value_map[nb].operands ]
        tmp[n] = min(n_expression)

    value_map = tmp
    value_map = {n: simplifier.simplifyMinExp(value_map[n], value_map[n].operands) for n in value_map }

time2 = time()
print "Algorithm Done... " + str(time2 - time1)

nice_print(value_map[nodes[0]])

"""
# Evaluate (Publicly)
time1 = time()
evaluator = BaseEvaluator(input_map)
value_map = {n : value_map[n].evaluate(evaluator) for n in value_map}

time2 = time()
print "Evaluated!! " + str(time2 - time1)
print "TOTAL TIME: " + str(time2 - time_)
#print ""
#print ""
"""

# Print the graph
#printGraph(nodes, edges_list, value_map)
