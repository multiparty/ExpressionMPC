from random import choice
from Expressions import V

def mapNodesToEdges(edges):
    mapping = {}
    for n1, n2, w in edges:
        mapping[n1] = mapping.get(n1, []) + [(n2, w)]
        mapping[n2] = mapping.get(n2, []) + [(n1, w)]

    return mapping

def mapNodesToEdgesWithWeights(edges, nodes):
    def process(s):
        return s[1:s.index("_")]

    mapping = {}
    for n1, n2, w in edges:
        if process(n1) == process(n2):
            continue

        mapping[n1] = mapping.get(n1, []) + [(n2, 1)]
        mapping[n2] = mapping.get(n2, []) + [(n1, 1)]

    for n1 in nodes:
        for n2 in nodes:
            if n1 == n2:
                continue

            if process(n1) == process(n2):
                w = n1 + ":" + n2
                if n1 > n2:
                    w = n2 + ":" + n1
                mapping[n1] = mapping.get(n1, []) + [(n2, V(w))]

    return mapping


def printGraph(nodes, edges, values, iteration=1):
    # Print out result
    # Print name
    print reduce(lambda x, y: x + y, [choice("ABCDEF0123456789") for i in range(8)]) + "("+str(iteration)+")"

    # Nodes
    print "states:"
    for n in nodes:
        v = str(values[n])
        n = str(n)
        print n+":"+v+";"

    # Edges
    print "transitions:"
    for e in edges:
        n0, n1, w = e
        n0 = str(n0)
        n1 = str(n1)
        w = (str(w) if w > 1 else "")
        print n0+":"+n1+":false:"+w+";"


def printGraphs(graphes):
    print "***MULTI***"
    for i in range(len(graphes)):
        n, e, v = graphes[i]
        printGraph(n, e, v, iteration=i+1)
        print "***END***"


def readGraph(definition):
    def fixW(w1, w2):
        w1 = w1.strip()
        w2 = w2.strip()
        if w1 < w2:
            return w1+":"+w2
        return w2+":"+w1

    definition = definition.strip()
    definition = definition.split("\n")
    for i in range(len(definition)):
        if definition[i].strip() == "states:" or definition[i].strip() == "States:":
            definition = definition[i+1:]
            break

    nodes = []
    edges = []
    values_map = {}

    # Read the nodes
    for i in range(len(definition)):
        node = definition[i].strip()
        if node == "transitions:" or node == "Transitions:":
            definition = definition[i+1:]
            break

        node = node[:-1].split(":")
        nodes.append(node[0]) # Name
        if node[1] == "inf":
            values_map[node[0]] = float("inf")
        elif node[1] == "X":
            values_map[node[0]] = "X"
        else:
            values_map[node[0]] = int(node[1]) # Value

    # Read the edges
    for edge in definition:
        edge = edge.strip()
        if edge == "":
            break

        edge = edge[:-1].split(":")
        w = edge[3].strip()
        if w == "":
            w = 1
        elif w == "inf":
            values_map[fixW(edge[0], edge[1])] = float("inf")
            w = V(fixW(edge[0], edge[1]))
        elif w == "X":
            values_map[fixW(edge[0], edge[1])] = w
            w = V(fixW(edge[0], edge[1]))
        else:
            values_map[fixW(edge[0], edge[1])] = int(w)
            w = V(fixW(edge[0], edge[1]))

        edges.append((edge[0].strip(), edge[1].strip(), w))

    return (nodes, edges, values_map)


def readGraphs(definitions):
    definitions = definitions.strip()
    if not definitions.startswith("***MULTI***"):
        return [ readGraph(definitions) ]

    definitions = definitions[len("***MULTI***"):]
    definitions.split("***END***")
    return [ readGraph(d) for d in definitions if len(d.strip()) > 0 ]


if __name__ == "__main__":
    test = """E766EFEB(1)
            States:
            0:6;
            1:7;
            2:7;
            3:8;
            4:2;
            Transitions:
            0:4:false:;
            1:4:false:2;
            1:2:false:2;
            2:3:false:;
            0:1:false:;
            0:4:false:;
            2:4:false:;
            1:2:false:;
            0:3:false:7;
            0:2:false:;"""

    printGraph(*(readGraphs(test))[0])
