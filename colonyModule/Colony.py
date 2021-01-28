import numpy as np
from multiprocessing import Process, Queue
from colonyModule.Ant import Ant


class Colony:
    """
      Defines a colony of ants

      Attributes:
        nodes: dict of nodes (key: (value1, value2))
        demand: vertices demand
        nest: initial node
        max_load: max load for each ant
        colony_size: number of ants in colony
        alpha: pheromone influence coefficient
        beta: distant influence coefficient
        rho: pheromone evaporation coefficient
        sigma: pheromone deposit coefficient
        iterations: stopping condition
        cost_function: a function to calculate the cost of a path
        pheromone_matrix: value of pheromone between nodes
        distance_matrix: value of distance between nodes

        nodes_size: number of nodes
        ants_list: list of the ants in the colony
    """

    def __init__(self, nodes, demand, nest, max_load, colony_size, alpha, beta, gamma, lam, rho, sigma, iterations, cost_function, pheromone_matrix, distance_matrix):
        self._nodes = nodes
        self._demand = demand
        self._nest = nest
        self._max_load = max_load
        self._colony_size = colony_size
        self._alpha = alpha
        self._beta = beta
        self._gamma = gamma
        self._lam = lam
        self._rho = rho
        self._sigma = sigma
        self._iterations = iterations
        self._cost_function = cost_function
        self._pheromone_matrix = pheromone_matrix
        self._distance_matrix = distance_matrix

        self._Q = Queue()
        self._nodes_size = len(nodes)

        if (self._pheromone_matrix == None):
            #self._pheromone_matrix = np.random.rand(self._nodes_size, self._nodes_size)
            #self._pheromone_matrix = np.full((self._nodes_size, self._nodes_size), (1/(self._nodes_size ** 2)))
            self._pheromone_matrix = np.full(
                (self._nodes_size, self._nodes_size), (5.0))

            # reset the main diagonal since there can't be pheromone traces going to a node itself
            np.fill_diagonal(self._pheromone_matrix, 0)

        self._ants_list = self._wake_ants()

    def _wake_ants(self):
        """
        Initialize ants for the first pass
        """
        return [Ant(self._nest, self._nodes, self._pheromone_matrix, self._distance_matrix,
                    self._cost_function, self._max_load, self._demand, self._alpha, self._beta, self._gamma, self._lam, self._Q) for _ in range(self._colony_size)]

    def _reset_ants(self):
        """
        Reset ants for a next pass (clear visited nodes)
        """
        for ant in self._ants_list:
            ant.reset_ant(self._nest, self._nodes, self._pheromone_matrix)

    def _evaporate_pheromones(self):
        for i in range(len(self._pheromone_matrix)):
            for j in range(len(self._pheromone_matrix)):
                if i != j:
                    self._pheromone_matrix[i][j] = (
                        1 - self._rho) * self._pheromone_matrix[i][j]

    def _update_pheromones(self, route, d_min, d1):
        for node, next_node in zip(route, route[1:]):
            new_pheromone_value = self._pheromone_matrix[node.id][next_node.id] + (
                self._sigma * (d_min / d1))
            if new_pheromone_value > 0.1 and new_pheromone_value < 5:
                self._pheromone_matrix[node.id][next_node.id] = new_pheromone_value

    def foraging(self):
        """
        Send ants to search food
        """
        best_solution = {"route": None, "cost": float("inf")}
        cnt_best_solution = 0

        for _ in range(self._iterations):
            best_iteration = {"route": None, "cost": float("inf")}

            for ant in self._ants_list:
                ant.start()

            for ant in self._ants_list:
                ant.join()

            for ant in self._ants_list:
                #route = ant.begin_route()
                route = self._Q.get()

                # if there isn't any solution
                if(route["route"] is None and route["cost"] is None):
                    return None

                # save best route for the current iteration
                if (route["cost"] < best_iteration["cost"]):
                    best_iteration = route

            # save best route for all the iterations
            if (best_iteration["cost"] < best_solution["cost"]):
                best_solution = best_iteration
                cnt_best_solution = 0
            else:
                cnt_best_solution += 1

            # evaporate pheromone
            self._evaporate_pheromones()

            # update pheromone
            for route in best_iteration["route"]:
                self._update_pheromones(
                    route, best_solution["cost"], best_iteration["cost"])

            self._reset_ants()

        return best_solution
