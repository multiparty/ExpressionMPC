
def concat_dir(directory, filename):
    directory = directory.strip()
    if not directory.endswith("/"):
        directory = directory + "/"
    
    return directory + filename

def read_parties(directory):
    directory = concat_dir(directory, "parties")
    with open(directory) as f:
        data = "".join(f.readlines())
        return [ int(s.strip()) for s in data.split(",") ]
    
def read_party(directory, party_id):
    directory = concat_dir(directory, party_id)
    with open(directory) as f:
        data = f.readlines()
        
        nodes = [ s.strip() for s in data[0].split(",") ]
        values = [ float("inf") if s.strip() == "inf" else int(s.strip()) for s in data[1].split(",") ]
        values = { nodes[i]: values[i] for i in range(len(nodes)) }

        diameter = int(data[2].strip())
        
        gateways = [ s.strip() for s in data[3].split(",") ]
        edges = [ (s.split(",")[0].strip(), s.split(",")[1].strip()) for s in data[4:] ]
        
        return nodes, values, diameter, gateways, edges
    
def read_public(directory):
    directory = concat_dir(directory, "public")
    with open(directory) as f:
        data = f.readlines()
        
        gateways = [ s.strip() for s in data[0].split(",") ]
        diameter = int(data[1].strip())
        edges = [ (s.split(",")[0].strip(), s.split(",")[1].strip()) for s in data[2:] ]
        
        return gateways, diameter, edges


def map_edges(nodes, edges):
    edges_map = { n: [] for n in nodes }
    for n1, n2 in edges:
        edges_map[n1].append(n2)
        edges_map[n2].append(n1)
    return edges_map
    
def map_gateways(parties, gateways):
    gateways_map = { p: [] for p in parties }
    for g in gateways:
        p = int(g[1:g.index("_")])
        gateways_map[p].append(g)
    return gateways_map
