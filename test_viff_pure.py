from optparse import OptionParser

import viff.reactor
viff.reactor.install()
from twisted.internet import reactor
from viff.config import load_config

from viff.field import GF
from viff.util import find_prime
from viff.comparison import *
from viff.runtime import Runtime, create_runtime, gather_shares, make_runtime_class

from graphs.graph_io import *
from time import clock as time
from collections import deque
import sys

# How to do min
def smin(x, y):
    #m = (x <= y)*x + (y <= x)*y
    m = y + (x <= y)*(x-y)
    return m
    
INFINITY=100000
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

directory = "graphs/AS_OREGON/bench5"
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

nodes = public_nodes
edges_map = public_edges
input_map = all_values
value_map = {} # holds outputs and intermidiate values between iterations

print "MPC Stage"
time1 = time()

# Initialize Viff
parser = OptionParser()
parser.set_defaults(modulus=2**65)

Runtime.add_options(parser)
options, args = parser.parse_args()
config_file = args[0]
id, parties = load_config(config_file)
parties_list = [p for p in parties]

# Sharing the inputs
def share_all(runtime):
    # Map node names by party id
    party_inputs = {p: [] for p in parties}
    for input_name in input_map:
        party = int(input_name[1:input_name.index("_")])
        party_inputs.get(party).append(input_name)

    # Sort the node names consistently in each party
    share_rounds = 0 # How many rounds to share all inputs
    for party in party_inputs:
        party_inputs[party].sort()
        share_rounds = max(share_rounds, len(party_inputs[party]))

    # Share the inputs in rounds
    shares = {} # will contain the shares.

    l = runtime.options.bit_length
    k = runtime.options.security_parameter
    Zp = GF(find_prime(2**65, blum=True))

    this_party_input = party_inputs[id]
    for i in range(share_rounds):
        value_to_share = 0
        if i < len(this_party_input):
            value_to_share = input_map[this_party_input[i]]
            value_to_share = INFINITY if value_to_share == float("inf") else value_to_share

        round_shares = runtime.shamir_share(parties_list, Zp, value_to_share)
        for index in range(len(round_shares)):
            party = parties_list[index]
            sharing_party_inputs = party_inputs[party]
            if i < len(sharing_party_inputs):
                shares[sharing_party_inputs[i]] = round_shares[index]

    return shares

# Actual Algorithm
def begin_MPC(runtime):
    try:
        print "Sharing..."
        shares = share_all(runtime)

        print "Executing..."
        global value_map
        value_map = {n: shares[n] for n in nodes} # All nodes are set to their shares
        i = 0
        for iteration in range(public_diameter): #Graph Distance Algorithm
            print "it" + str(i)
            i = i + 1
            tmp = {}
            j = 0
            for n in nodes:
                print "node" + str(j) 
                j = j + 1
                val = value_map[n]
                for nb in edges_map[n]:
                    val = smin(val, value_map[nb] + 1 ) # Open Weight (1)
                
                for nb in gateways_per_party[get_party(n)]:
                    if nb == n: continue
                    w = (nb+":"+n) if nb < n else (n+":"+nb)
                    val = smin(val, value_map[nb] + shares[str(w)] ) # Secret Distance

                tmp[n] = val
            value_map = tmp

        print "Algorithm Done..."

        results = []
        gathered = []
        for node_name in value_map:
            party = get_party(node_name)
            share = runtime.open(value_map[node_name], receivers=[party])
            if share is not None:
                gathered.append(share)
                results.append(node_name)
            else:
                value_map[node_name] = "X"

        def results_ready(opened_results):
            print "Results Ready"
            for i in range(len(opened_results)):
                node_name = results[i]
                value_map[node_name] = opened_results[i] if opened_results[i] < INFINITY else float("inf")

        gathered = gather_shares(gathered)
        gathered.addCallback(results_ready)
        print "Opening"

        runtime.schedule_callback(gathered, lambda _: runtime.shutdown())
    except:
        import traceback
        traceback.print_exc()

# Intialize Runtime
runtime_class = make_runtime_class(mixins=[ComparisonToft07Mixin])
pre_runtime = create_runtime(id, parties, 1, options, runtime_class)
pre_runtime.addCallback(begin_MPC)

# Start the Twisted event loop.
reactor.run()

print "Evaluated!!"
time2 = time()

print "MPC TIME: " + str(time2 - time1)
print "TOTAL TIME: " + str(time2 - time_)

