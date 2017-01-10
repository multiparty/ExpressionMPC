from Expressions import *
from RandomGraphGen import *
from GraphIO import *

# Initialize Graph
nodes, edges_list = genGraph(7, 7, 10, 15, 15, 3)
edges_list = genWeights(edges_list)
edges_map = mapNodesToEdges(edges_list)
input_map = genValues(nodes) # Actual Input Values

printGraph(nodes, edges_list, input_map)
