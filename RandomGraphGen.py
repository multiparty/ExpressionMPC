from random import randint, choice, random

def addEdge(n0, n1, edges, counts):
    if n0 > n1:
        tmp = n0
        n0 = n1
        n1 = tmp

    edges.append( (n0, n1) )
    counts[n0] = counts[n0] + 1
    counts[n1] = counts[n1] + 1


def genGraph(minN, maxN, minE, maxE, D, parties=None):
    # Choose random node and edge count
    N = randint(minN, maxN)
    E = randint(minE, maxE)

    # Holds the result
    nodes = [str(n) for n in range(N)]
    edges = []

    # Determine the parties of the nodes
    if parties is None:
        nodes = [ "P" + n + "_" + n for n in nodes ]
    else:
        n = 0
        for p in range(parties):
            min_num = (1 if p < parties - 1 else len(nodes) - n)
            num_for_p = randint(min_num, (len(nodes) - n) - (parties - p - 1))

            for i in range(num_for_p):
                nodes[n] = "P"+str(p)+"_"+str(i)
                n = n + 1

    counts = {n: 0 for n in nodes} # Tracks Degree of Nodes

    # Ensure graph is connected (by creating a chain-path)
    last = nodes[0]
    nodes_copy = nodes[1:]
    while len(nodes_copy) > 0:
        next = choice(nodes_copy)
        nodes_copy.remove(next)
        addEdge(last, next, edges, counts)
        last = next
        E = E - 1

    # Add E random edges according to constraints.
    possibleEdges = [(n0, n1) for n0 in nodes for n1 in nodes if n1 > n0]
    while E > 0 and len(possibleEdges) > 0:
        edge = choice(possibleEdges)
        possibleEdges.remove(edge)

        if counts[edge[0]] >= D:
            continue
        if counts[edge[1]] >= D:
            continue

        addEdge(edge[0], edge[1], edges, counts)
        E = E - 1

    return nodes, edges


def genValues(nodes, min=0, max=10, inf=True):
    possibilities = [ i for i in range(min, max) ] + ( [ float('inf') ] if inf else [] )
    values = {n: choice(possibilities) for n in nodes}

    return values


def genWeights(edges, min=2, max=10):
    result = []
    for n1, n2 in edges:
        w = 1
        if n1.split("_")[0] == n2.split("_")[0]: # If belong to same party.
            w = randint(min, max)
        result.append((n1, n2, w))

    return result


if __name__ == "__main__":
    import sys

    # Read Args From Command Line
    minN = int(sys.argv[1])
    maxN = int(sys.argv[2])
    minE = int(sys.argv[3])
    maxE = int(sys.argv[4])
    parties = (int(sys.argv[5]) if len(sys.argv) > 5 else None)
    D = (int(sys.argv[6]) if len(sys.argv) > 6 else maxE)

    nodes, edges = genGraph(minN, maxN, minE, maxE, D, parties)
    values = genValues(nodes)
    edges = genWeights(edges)

    from GraphIO import printGraph
    printGraph(nodes, edges, values)
