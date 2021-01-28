import time
import re
import numpy as np
from colonyModule.Node import Node
from colonyModule.Colony import Colony


def read_dataset(path):
    dataset = open(path, "r")

    i = 0

    while True:
        line = dataset.readline()

        if not line:
            break

        if(i == 0):
            n_nodes = int(line)
            costs = {(i, j): 0 for i in range(n_nodes) for j in range(n_nodes)}
        elif(i == 1):
            demand = [int(q) for q in line.split()]
        elif(i == 2):
            capacity_vehicles = int(line)
        else:
            j = 0
            for el in line.split():
                costs[(i-3, j)] = float(el)
                j = j+1

        i = i+1

    dataset.close()

    return (n_nodes, costs, demand, capacity_vehicles)


def test_datasets(datasets, colony_size, alpha, beta, gamma, lam, rho, sigma, iterations):
    solutions = []
    for dataset in datasets:
        n_nodes, cost_dict, demand, max_load = read_dataset(dataset["file"])
        nodes = []

        for i in range(n_nodes):
            nodes.extend([Node(i)])

        def cost_function(from_node, to_node):
            return cost_dict[(from_node.id, to_node.id)]

        cost_matrix = np.array(list(cost_dict.values())).reshape(n_nodes, n_nodes)

        try:
            colony = Colony(nodes, demand, nodes[0], max_load, colony_size, alpha, beta,
                            gamma, lam, rho, sigma, iterations, cost_function, None, cost_matrix)
            start = time.time()
            solution = colony.foraging()
            end = time.time()
            datasetName = re.sub(r"\/.*\/", "", dataset["file"])
            solution["dataset"] = datasetName
            solution["time"] = round(end-start, 2)
            solution["gap"] = round(
                (((solution["cost"]/dataset["best"])-1)*100), 2)
            solution["route"] = [node.id for route in solution["route"]
                                 for node in route]
            solutions.append(solution)
            print(datasetName + " ok")
        except IndexError as e:
            print(datasetName + " no", e)

    return solutions


if __name__ == "__main__":
    datasets = [{"file": "dataset/parma5.txt", "best": 19500},
                {"file": "dataset/bergamo5.txt", "best": 7900},
                {"file": "dataset/parma8.txt", "best": 22700},
                {"file": "dataset/bergamo8.txt", "best": 10400},
                {"file": "dataset/parma9.txt", "best": 23400},
                {"file": "dataset/bergamo9.txt", "best": 10200},
                {"file": "dataset/parma10.txt", "best": 25400},
                {"file": "dataset/bergamo10.txt", "best": 10800}]

    datasets += [{"file": "dataset/1Bari30.txt", "best": 14600},
                 {"file": "dataset/2Bari20.txt", "best": 15700},
                 {"file": "dataset/3Bari10.txt", "best": 20600},
                 {"file": "dataset/4ReggioEmilia30.txt", "best": 16900},
                 {"file": "dataset/5ReggioEmilia20.txt", "best": 23200},
                 {"file": "dataset/6ReggioEmilia10.txt", "best": 32500},
                 {"file": "dataset/7Bergamo30.txt", "best": 12600},
                 {"file": "dataset/8Bergamo20.txt", "best": 12700},
                 {"file": "dataset/9Bergamo12.txt", "best": 13500},
                 {"file": "dataset/10Parma30.txt", "best": 29000},
                 {"file": "dataset/11Parma20.txt", "best": 29000},
                 {"file": "dataset/12Parma10.txt", "best": 32500},
                 {"file": "dataset/13Treviso30.txt", "best": 29259},
                 {"file": "dataset/14Treviso20.txt", "best": 29259},
                 {"file": "dataset/15Treviso10.txt", "best": 31443},
                 {"file": "dataset/16LaSpezia30.txt", "best": 20746},
                 {"file": "dataset/17LaSpezia20.txt", "best": 20746},
                 {"file": "dataset/18LaSpezia10.txt", "best": 22811},
                 {"file": "dataset/19BuenosAires30.txt", "best": 76999},
                 {"file": "dataset/20BuenosAires20.txt", "best": 91619},
                 {"file": "dataset/21Ottawa30.txt", "best": 16202},
                 {"file": "dataset/22Ottawa20.txt", "best": 16202},
                 {"file": "dataset/23Ottawa10.txt", "best": 17576}]

    solutions = test_datasets(datasets, colony_size=50, alpha=6,
                              beta=5, gamma=5, lam=5, rho=0.4, sigma=1, iterations=100)

    print("\n")

    for solution in solutions:
        print(solution["dataset"], solution["cost"],
              solution["time"], solution["gap"])
