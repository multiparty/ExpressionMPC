from Expressions import *
from Simplifiers import AgressiveRedundantMinSimplifier
from EvaluatorsViff import ViffEvaluator, INFINITY
from graphs.graph_io import *

from collections import deque

from time import clock as time
import sys

sys.setrecursionlimit(10000)

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
    
def get_party(g):
    return int(g[1:g.index("_")])

"""
INITIALIZATION
"""
time_ = time()

directory = "graphs/AS_OREGON/bench7"
ID = sys.argv[2]
ID = int(ID[ID.index("-")+1:ID.index(".")])
ID = str(ID)
print ID

parties = read_parties(directory)
nodes, values, diameter, gateways, edges = read_party(directory, ID)
public_nodes, public_diameter, public_edges = read_public(directory)

edges = map_edges(nodes, edges)
public_edges = map_edges(public_nodes, public_edges)
gateways_per_party = map_gateways(parties, public_nodes)

time2 = time()
print "Initialized... " + str(time2 - time_)

"""
LOCAL STAGE
"""
print "Local Stage 1"
time1 = time()

# Network distance
for d in range(diameter):
    tmp = {}
    for n in nodes:
        tmp[n] = min(values[n], min([ values[n2] for n2 in edges[n]]))
        
    values = tmp

# shortest pathes between gateways
distances = { n: {} for n in gateways }
for n1 in gateways:
    visited = set()
    queue = deque([ (n1, 0) ])
    remaining = { g for g in gateways if g != n1 }
    while len(remaining) > 0 and len(queue) > 0:
        n, d = queue.popleft()
        
        if n in visited: continue
        visited.add(n)
        
        for n2 in edges[n]:
            if n2 in visited: continue
            queue.append( (n2, d+1) )
            
            if n2 in remaining:
                distances[n1][n2] = d + 1
                remaining.remove(n2)                                                                                                                                                                                                                                                                   

# Weights and Values for this party's gateways
all_values = { n: None for n in public_nodes}
all_weights = {}
for p in parties:
    p_gateways = gateways_per_party[p]
    for g1 in range(len(p_gateways) - 1):
        for g2 in range(g1+1, len(p_gateways)):
            gt1, gt2 = p_gateways[g1], p_gateways[g2]
            if gt1 < gt2: all_weights[gt1+":"+gt2] = None
            elif gt1 > gt2: all_weights[gt2+":"+gt1] = None
all_values.update(all_weights)

gateway_values = { n: min(values[n], INFINITY) for n in gateways}
gateway_weights = {}
for g1 in range(len(gateways) - 1):
    for g2 in range(g1+1, len(gateways)):
        gt1, gt2 = gateways[g1], gateways[g2]
        if gt1 < gt2: gateway_weights[gt1+":"+gt2] = min(distances[gt1][gt2], INFINITY)
        elif gt1 > gt2: gateway_weights[gt2+":"+gt1] = min(distances[gt1][gt2], INFINITY)
gateway_values.update(gateway_weights)
all_values.update(gateway_values)

time2 = time()
print "1st Local... " + str(time2 - time1)

"""
MPC STAGE
"""

print "MPC Stage"
time1 = time()

# Simplifiers
simplifier = AgressiveRedundantMinSimplifier()
AddExp.addCompare = staticmethod(compare)

# Initial "Symbolic" Values
time1 = time()
mpc_value_map = {n: min([V(n)]) for n in public_nodes} # V -> FreeVarExp
for iteration in range(public_diameter): # Graph Distance Algorithm
    print iteration
    tmp = {}
    for n in public_nodes:
        n_expression = mpc_value_map[n].operands
        for nb in public_edges[n]:
            n_expression = n_expression + [ o + 1 for o in mpc_value_map[nb].operands ]
        
        """   
        for nb in gateways_per_party[get_party(n)]:
            if nb == n: continue
            w = (nb+":"+n) if nb < n else (n+":"+nb)
            n_expression = n_expression + [ o + V(w) for o in mpc_value_map[nb].operands ]
        """

        tmp[n] = min(n_expression)

    mpc_value_map = tmp
    mpc_value_map = {n: simplifier.simplifyMinExp(mpc_value_map[n], mpc_value_map[n].operands) for n in mpc_value_map }
    
weight_expressions = {}
for n in public_nodes:
    n_expression = [V(n)]
    for nb in gateways_per_party[get_party(n)]:
        if nb == n: continue
        w = (nb+":"+n) if nb < n else (n+":"+nb)
        n_expression.append(V(nb) + V(w))
    weight_expressions[n] = min(n_expression)

time2 = time()
print "Algorithm/Simplification Done... " + str(time2 - time1)

# Evaluate (Securely)
time1_ = time()
mpc_value_map = { n: (get_party(n), mpc_value_map[n]) for n in mpc_value_map } 
value_map = ViffEvaluator.evaluate(all_values, mpc_value_map, weight_expressions)

time2 = time()
print "Evaluated!! " + str(time2 - time1_)
print "2nd Mpc... " + str(time2 - time1)

"""
LOCAL STAGE 2
"""

print "Local Stage 2"
time1 = time()

for v in value_map: # integrate new values
    if get_party(v) == ID:
        values[v] = value_map[v]

# Network distance
for d in range(diameter):
    tmp = {}
    for n in nodes:
        tmp[n] = min(values[n], min([ values[n2] for n2 in edges[n]]))
        
    values = tmp
    
time2 = time()
print "3rd Local... " + str(time2 - time1)
print "TOTOAL TIME: " + str(time2 - time_)



