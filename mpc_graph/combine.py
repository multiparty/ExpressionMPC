import sys

if __name__ == "__main__":
    fname_global = sys.argv[1]
    fname_locals = sys.argv[2:]

    with open(fname_global) as f:
        content = f.readlines()
        content = filter(lambda x: len(x) >= 0, map(lambda x: x.strip(), content))

        header = content[0]
        proxy_edges = ""
        transitions_index = 0
        for i in range(len(content)):
            if content[i] == "transitions:":
                transitions_index = i
                break
        # proxy edges
        for i in range(transitions_index+1, len(content)):
            line = content[i]
            name1 = line.split(":")[0]
            player1 = name1[1:name1.index("_")]
            name2 = line.split(":")[1]
            player2 = name2[1:name2.index("_")]

            if player1 != player2:
                proxy_edges = proxy_edges + line + "\n"

    allNodes = ""
    allEdges = ""
    for fname in fname_locals:
        with open(fname) as f:
            content = f.readlines()
            content = filter(lambda x: len(x) >= 0, map(lambda x: x.strip(), content))

            header = content[0]
            states_index = 1
            transitions_index = 0
            for i in range(len(content)):
                if content[i] == "transitions:":
                    transitions_index = i
                    break

            for i in range(states_index+1, transitions_index):
                allNodes = allNodes + content[i] + "\n"

            for i in range(transitions_index+1, len(content)):
                allEdges = allEdges + content[i] + "\n"

    with open("output.txt", 'w') as o:
        o.truncate()
        o.write(header + "\n")
        o.write("states:" + "\n")
        o.write(allNodes)
        o.write("transitions:" + "\n")
        o.write(allEdges)
        o.write(proxy_edges)
