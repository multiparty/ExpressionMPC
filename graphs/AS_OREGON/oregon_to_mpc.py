import random
import os

import networkx as nx

def compute_diameter(nodes, edges):
    distances = { n: { n1: float("inf") for n1 in nodes } for n in nodes }

    for n in nodes:
        distances[n][n] = 0
        
    for n1, n2 in edges:
        distances[n1][n2] = 1
        distances[n2][n1] = 1
    
    for k in nodes:
        for i in nodes:
            for j in nodes:
                if distances[i][k] + distances[k][j] < distances[i][j]:
                    distances[i][j] = distances[i][k] + distances[k][j]
                    
    diameter = 0
    for n1 in nodes:
        for n2 in nodes:
            if distances[n1][n2] < float("inf"): 
                diameter = max(diameter, distances[n1][n2])
    
    return diameter

def get_party(n):
    return int(n[1:n.index("_")])

def transform_one_to_local(filename, party_id, number_of_gateways):
    prefix = "P"+str(party_id)+"_"
    number_nodes = 0
    number_edges = 0
    date_of_file = ""
    
    nodes = set()
    edges = []
    diameter = 0
    with open(filename, 'r') as f:
        line_counter = 0
        for line in f:
            if line_counter < 4:
                if line_counter == 0:
                    diameter = int(line[len("# "):].strip())
                elif line_counter == 1:
                    date_of_file = line
                elif line_counter == 2:
                    l = line[len("# Nodes: "):].split(" Edges: ")
                    number_nodes, number_edges = int(l[0]), int(l[1])
                    #nodes = [ prefix + str(n) for n in xrange(1, number_nodes+1)]
            else: #reading edges:
                line = line.strip()
                if len(line) > 0:
                    l = line.split()
                    n1, n2 = l[0], l[1]
                    edges.append( (prefix+n1, prefix+n2) )
                    nodes.add(prefix+n1)
                    nodes.add(prefix+n2)
        
            line_counter = line_counter + 1
            
    nodes = list(nodes)            
    values = [ (0 if random.random() < 0.15 else float("inf")) for n in nodes ]
    gateways = random.sample(nodes, min(number_of_gateways, len(nodes)))
    return (nodes, values, diameter, edges), gateways, date_of_file


def transform_all(filenames, party_ids, min_gateways, max_gateways, edges):
    comments = []
    
    all_gateways = []    
    graphs, gateways_map = {}, {}
    for i in range(len(filenames)):
        fname, p = filenames[i], party_ids[i]
        g = random.randint(min_gateways, max_gateways)
        
        graph, gateways, comment = transform_one_to_local(fname, p, g)
        graphs[p] = graph
        gateways_map[p] = gateways
        all_gateways = all_gateways + gateways
        comments.append(comment)
        
    # Generate the public graph using scale-free distribution
    s = nx.utils.powerlaw_sequence(len(all_gateways), 1.7)
    G = nx.expected_degree_graph(s, selfloops=False)
    
    public_edges = []
    for n1, n2 in G.edges():
        g1, g2 = all_gateways[n1], all_gateways[n2]
        if get_party(g1) == get_party(g2): continue
        public_edges.append( (g1, g2) )
    
    print len(all_gateways), len(public_edges)
    return graphs, gateways_map, (all_gateways, compute_diameter(all_gateways, public_edges), public_edges), comments
        

def write_out(directory, parties, graphes, gateways_map, public_graph, comments):
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
    f.write("\n")
    f.write("\n")
    f.write( ("".join(comments)) + "\n")
    f.close()


if __name__ == "__main__":
    import sys

    min_g, max_g = int(sys.argv[1]), int(sys.argv[2])
    min_e, max_e = int(sys.argv[3]), int(sys.argv[4])
    directory = sys.argv[5]
    files = sys.argv[6:]
    parties = range(1, len(files) + 1)

    g, gm, pg, comments = transform_all(files, parties, min_g, max_g, random.randint(min_e, max_e))
    write_out(directory, parties, g, gm, pg, comments)
        
        
