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

directory = "graphs/AS_OREGON/bench2"
ID = sys.argv[2]
ID = int(ID[ID.index("-")+1:ID.index(".")])
ID = str(ID)
print ID

parties = read_parties(directory)
_, public_diameter, public_edges = read_public(directory)
public_nodes, all_values, nodes_per_party = [], {}, {}
for party in parties:
    nodes, values, diameter, _, edges = read_party(directory, str(party))
    public_nodes += nodes
    public_diameter += diameter
    public_edges += edges
    
    nodes_per_party[int(party)] = nodes
    if str(ID) == str(party): # only read own party's inputs
        all_values = values
    
nodes, diameter, edges, values = public_nodes, public_diameter, public_edges, all_values
public_nodes, public_diameter, public_edges, all_values = None, None, None, None

edges = map_edges(nodes, edges)

time2 = time()
print "Initialized... " + str(time2 - time_)


""" 
MPC STAGE
"""

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
    share_rounds = 0 # How many rounds to share all inputs
    for party in nodes_per_party:
        share_rounds = max(share_rounds, len(nodes_per_party[party]))

    # Share the inputs in rounds
    shares = {} # will contain the shares.

    l = runtime.options.bit_length
    k = runtime.options.security_parameter
    Zp = GF(find_prime(2**65, blum=True))

    this_party_input = nodes_per_party[int(id)]
    for i in range(share_rounds):
        print "share round " + str(i) + "/" + str(share_rounds)
        value_to_share = 0
        if i < len(this_party_input):
            value_to_share = values[this_party_input[i]]
            value_to_share = INFINITY if value_to_share == float("inf") else value_to_share

        round_shares = runtime.shamir_share(parties_list, Zp, value_to_share)
        for index in range(len(round_shares)):
            party = parties_list[index]
            sharing_party_inputs = nodes_per_party[int(party)]
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
        for iteration in range(diameter): #Graph Distance Algorithm
            tmp = dict(value_map)
            # Print Iteration Number
            i, j = i + 1, 0
            print "it" + str(i) + "/" + str(diameter)
            
            # Compute new distance value for a node n
            for n in nodes:
                # Print Node Number
                j = j + 1
                print "node" + str(j) +"/" + str(len(nodes))
                
                val = value_map[n]
                for nb in edges[n]:
                    val = smin(val, value_map[nb] + 1 ) # Naive, no private weights.

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
        runtime.schedule_callback(gathered, lambda _: runtime.shutdown())
        print "Opening"
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

