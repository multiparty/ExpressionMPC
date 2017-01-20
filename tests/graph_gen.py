import random
import os

def compute_diameter(nodes, edges):
    distances = { n: { n1: float(inf) for n1 in nodes } for n in nodes }

    for n in nodes:
        distances[n][n] = 0
        
    for n1, n2 in edges:
        distances[n1][n2] = 1
        distances[n2][n1] = 1
    
    for k in nodes:
        for i in nodes:
            for j in nodes:
                if A[i][k] + A[k][j] < A[i][j]:
                    A[i][j] = A[i][k] + A[k][j]
                    
    diameter = 0
    for n1 in nodes:
        for n2 in nodes:
            diameter = max(diameter, distances[n1][n2])
    
    return diameter

# generate a simple graph given the number of nodes and edges.
def gen_local_graph(prefix, n, e):
    prefix = prefix + "_"

    nodes_list = [ prefix + str(n+1) for n in range(n) ]
    values_list = [ 0 if random.random() < 0.33 else "inf" for n in range(n) ]
    edges_list = [ (nodes_list[i], nodes_list[i+1]) for i in range(len(nodes_list) - 1) ]
    all_edges = { (nodes_list[i], nodes_list[j]) for i in range(len(nodes_list) - 1) for j in range(i, len(nodes_list)) if abs(i - j) > 1 }

    e = e - len(edges_list)
    if e >= len(all_edges): # pick all edges
        edges_list = edges_list + list(all_edges)
    elif e > 0: # pick e edges
        edges_list = edges_list + random.sample(all_edges, e)

    return nodes_list, values_list, edges_list

# generate edges given nodes and number of desired edges.
# the nodes are stored in lists, each list is mapped to its party number.
def gen_edges(parties, nodes, e):
    all_edges = set() # Compute all possible edges belonging to different parties.
    for p1 in range(len(parties) - 1):
        for p2 in range(p1+1, len(parties)):
            n1, n2 = nodes[parties[p1]], nodes[parties[p2]]
            for e1 in n1:
                for e2 in n2:
                    all_edges.add( (e1, e2) )

    edges_list = [] # Ensure graph is connected
    for p1 in range(len(parties) - 1):
        p1, p2 = nodes[parties[p1]], nodes[parties[p1 + 1]]
        edg = ( random.choice(p1), random.choice(p2) )
        edges_list.append(edg)
        all_edges.remove(edg)
        e = e - 1

    if e >= len(all_edges): # Pick All edges.
        edges_list = edges_list + list(all_edges)
    elif e > 0: # Pick e edges.
        edges_list = edges_list + random.sample(all_edges, e)

    return edges_list

# Generate the entire graph
# Given the number of parties.
# Minimum and Maximum nodes per party.
# Minimum and Maximum edges per party.
# Minimum and Maximum Gateways per party.
# Minimum and Maximum edges in the public graph
def gen_whole_graph(p, min_n, max_n, min_e, max_e, min_g, max_g, min_pe, max_pe):
    graphes = {}
    gateways_map = {}
    gateways = []

    parties_list = [ i + 1 for i in range(p) ]
    for p in parties_list:
        n = random.randint(min_n, max_n)
        e = random.randint(min_e, max_e)

        n, v, e = gen_local_graph("P"+str(p), n, e)
        graphes[p] = (n, v, compute_diameter(n, e), e)

        g = random.randint(min_g, max_g)
        g = random.sample(n, g)
        gateways = gateways + g
        gateways_map[p] = g

    e = random.randint(min_pe, max_pe)
    e = gen_edges(parties_list, gateways_map, e)
    return ( parties_list, graphes, gateways_map, (gateways, compute_diameter(gateways, e), e) )

def write_out(directory, parties, graphes, gateways_map, public_graph):
    total_nodes, total_edges, public_nodes, public_edges = 0, 0, 0, 0

    directory = directory.strip()
    if not os.path.exists(directory): os.makedirs(directory)
    if not directory[-1] == '/': directory = directory + "/"

    # Write out the parties
    f = open(directory + "parties", "w+")
    f.write( (",".join([ str(p) for p in parties])) + "\n")
    f.close()

    # Write out each party's graph
    for p in parties:
        # Stats.
        n, v, d, e = graphes[p]
        total_nodes = total_nodes + len(n)
        total_edges = total_edges + len(e)

        # Write out party graph.
        f = open(directory + str(p), 'w+')
        f.write( (",".join(n)) + "\n" )
        f.write( (",".join([ str(vv) for vv in v ])) + "\n" )
        f.write( str(d) + "\n" )
        f.write( (",".join(gateways_map[p])) + "\n" )

        for e1, e2 in e:
            f.write(e1 + "," + e2 + "\n")

        f.close()

    # Stats.
    n, d, e = public_graph
    public_nodes = len(n)
    public_edges = len(e)

    # Write out public graph.
    f = open(directory + "public", "w+")
    f.write( (",".join(n)) + "\n" )
    f.write( str(d) + "\n" )

    for e1, e2 in e:
        f.write(e1 + "," + e2 + "\n")
    f.close()

    # Write out the specs.
    f = open(directory + "specs", "w+")
    f.write("parties: " + str(len(parties)) + "\n")
    f.write("nodes: " + str(total_nodes) + "\n")
    f.write("edges: " + str(total_edges) + "\n")
    f.write("public nodes: " + str(public_nodes) + "\n")
    f.write("public edges: " + str(public_edges) + "\n")
    f.close()

if __name__ == "__main__":
    import sys

    p = int(sys.argv[1])
    min_n, max_n, min_e, max_e = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    min_g, max_g, min_pe, max_pe = int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]), int(sys.argv[9])
    directory = sys.argv[10]

    p, g, gm, pg = gen_whole_graph(p, min_n, max_n, min_e, max_e, min_g, max_g, min_pe, max_pe)
    write_out(directory, p, g, gm, pg)
