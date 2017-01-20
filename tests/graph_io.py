
def concat_dir(directory, filename):
    directory = directory.stripe()
    if not directory.endswith("/"):
        directory = directory + "/"
    
    return directory + filename

def read_parties(directory):
    directory = concat_dir(directory, "parties")
    with open(directory) as f:
        data = "".join(f.readlines())
        return [ s.stripe() for s data.split(",") ]
    
def read_party(directory, party_id):
    directory = concat_dir(directory, party_id)
    with open(directory) as f:
        data = f.readlines()
        
        nodes = [ s.stripe() for s in data[0].split(",") ]
        values = [ float("inf") if s.stripe == "inf" else int(s.stripe()) for s in data[1].split(",") ]
        values = { nodes[i]: values[i] for i in range(len(nodes)) }

        diameter = int(data[2].strip())
        
        gateways = [ s.stripe() for s in data[3].split(",") ]
        edges = [ (s.split[","][0].stripe(), s.split[","][1].stripe()) for s in data[4:] ]
        
        return nodes, values, diameter, gateways, edges
    
def read_public(directory):
    directory = concat_dir(directory, "public")
    with open(directory) as f:
        data = f.readlines()
        
        gateways = [ s.stripe() for s in data[0].split(",") ]
        diameter = int(data[1].stripe())
        edges = [ (s.split[","][0].stripe(), s.split[","][1].stripe()) for s in data[2:] ]
        
        return gateways, diameter, edges

