from Expressions import *
from RandomGraphGen import *
from GraphIO import *
from Simplifiers import *
from Evaluators import BaseEvaluator

from time import clock as time
import sys


def print_map(e):
    print "MAP"
    for k in e:
        print str(k) + " : " + str(e[k])
    print ""

def nice_print(e):
    ops = e.operands
    
    def compare(o1, o2):
        o1 = o1.operands
        o2 = o2.operands
        
        for i in range(min(len(o1), len(o2))):
            s1, s2 = str(o1[i]), str(o2[i])
            if s1 < s2:
                return -1
            if s2 < s1:
                return 1
        
        return len(o1) - len(o2)
        
    print "MIN("
    for o in sorted(ops, cmp=compare):
        print "\t"+str(o)
    print ")"
    print  ""

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
