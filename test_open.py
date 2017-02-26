from graphs.graph_io import *
from time import clock as time
import sys

sys.setrecursionlimit(10000)

"""
INITIALIZATION
"""
time_ = time()

directory = "graphs/AS_OREGON/bench" + sys.argv[1]

parties = read_parties(directory)
_, public_diameter, public_edges = read_public(directory)
public_nodes, value_map = [], {}
for party in parties:
    nodes, values, diameter, _, edges = read_party(directory, str(party))
    public_nodes += nodes
    public_diameter += diameter
    public_edges += edges
    value_map.update(values)
    
nodes, diameter, edges = public_nodes, public_diameter, public_edges
public_nodes, public_diameter, public_edges = None, None, None

edges = map_edges(nodes, edges)

time2 = time()
print "Initialized... " + str(time2 - time_)


""" 
(OPEN/PUBLIC) COMPUTATION STAGE
"""

print "Open Stage"
time1 = time()

for iteration in range(diameter): #Graph Distance Algorithm
    tmp = {}
    
    # Print Iteration Number
    print "it" + str(iteration) + "/" + str(diameter)
    
    # Compute new distance value for a node n
    for n in nodes:        
        val = value_map[n]
        for nb in edges[n]:
            val = min(val, value_map[nb] + 1) # Public, no private weights.

        tmp[n] = val
    value_map = tmp

print "Algorithm Done..."

print "Evaluated!!"
time2 = time()

print "OPEN TIME: " + str(time2 - time1)
print "TOTAL TIME: " + str(time2 - time_)

