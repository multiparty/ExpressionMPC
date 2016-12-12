import sys

if __name__ == "__main__":
    fname = sys.argv[1]

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

    outputs = {}

    # nodes
    for i in range(states_index+1, transitions_index):
        line = content[i]
        name = line.split(":")[0]
        player = name[1:name.index("_")]

        if not player in outputs:
            outputs[player] = "Kripke Structure ("+player+")" + "\n" + "states:" + "\n"
        outputs[player] = outputs[player] + line + "\n"

    outputs = { o: outputs[o] + "transitions:" + "\n" for o in outputs }

    # edges
    for i in range(transitions_index+1, len(content)):
        line = content[i]
        name1 = line.split(":")[0]
        player1 = name1[1:name1.index("_")]
        name2 = line.split(":")[1]
        player2 = name2[1:name2.index("_")]

        if player1 == player2:
            outputs[player1] = outputs[player1] + line + "\n"

    for player in outputs:
        with open(player+".txt", 'w') as o:
            o.truncate()
            o.write(outputs[player])
