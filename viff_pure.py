from GraphIO import *

from optparse import OptionParser

import viff.reactor
viff.reactor.install()
from twisted.internet import reactor
from viff.config import load_config

from viff.field import GF
from viff.util import find_prime
from viff.comparison import *
from viff.runtime import Runtime, create_runtime, gather_shares, make_runtime_class

from time import clock as time
import sys

# How to do min
def smin(x, y):
    m = (x <= y)*x + (y <= x)*y
    return m

# Initialize Graph
time1 = time()

ID = sys.argv[2]
ID = int(ID[ID.index("-")+1:ID.index(".")]) - 1
ID = str(ID)
nodes, edges_list, input_map = readGraph(open('mpc_graph/2MPC/input'+ID+'.txt', 'r').read())
edges_map = mapNodesToEdges(edges_list)
value_map = {}

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
        party_inputs.get(party+1).append(input_name)

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

        round_shares = runtime.shamir_share(parties_list, Zp, value_to_share)
        for index in range(len(round_shares)):
            party = parties_list[index]
            sharing_party_inputs = party_inputs[party]
            if i < len(sharing_party_inputs):
                shares[sharing_party_inputs[i]] = round_shares[index]

    return shares

# Actual Algorithm
def begin_MPC(runtime):
    print "Sharing..."
    shares = share_all(runtime)

    print "Executing..."
    global value_map
    value_map = {n: shares[n] for n in nodes} # All nodes are set to their shares
    for iteration in range(len(nodes)): #Graph Distance Algorithm
        tmp = {}
        for n in nodes:
            print "."
            val = value_map[n]
            for nb, w in edges_map[n]:
                if isinstance(w, int): val = smin(val, value_map[nb] + w ) # Open Weight (1)
                else: val = smin(val, value_map[nb] + shares[str(w)] ) # Secret Distance

            tmp[n] = val

        value_map = tmp

    print "Algorithm Done..."

    results = []
    gathered = []
    for node_name in value_map:
        party = int(node_name[1:node_name.index("_")])
        share = runtime.open(value_map[node_name], receivers=[party+1])
        if share is not None:
            gathered.append(share)
            results.append(node_name)
        else:
            value_map[node_name] = "X"

    def results_ready(opened_results):
        print "RESULTS READY"
        for i in range(len(opened_results)):
            node_name = results[i]
            value_map[node_name] = opened_results[i]

    gathered = gather_shares(gathered)
    gathered.addCallback(results_ready)
    print "GATHERED"

    runtime.schedule_callback(gathered, lambda _: runtime.shutdown())

# Intialize Runtime
runtime_class = make_runtime_class(mixins=[ComparisonToft07Mixin])
pre_runtime = create_runtime(id, parties, 1, options, runtime_class)
pre_runtime.addCallback(begin_MPC)

# Start the Twisted event loop.
reactor.run()

print "Evaluated!!"
print "TOTAL TIME: " + str(time() - time1)
print ""
print ""

# Print the graph
printGraph(nodes, edges_list, value_map)
