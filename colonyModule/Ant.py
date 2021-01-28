from heapq import nlargest
import random
import itertools
from multiprocessing import Process, Queue
from colonyModule import utils


class Ant(Process):
    """
    Creates an Ant

    Each ant visits all the nodes

    Parameters:
      current_node: current node where the ant is
      unvisited_nodes: a list of nodes that the ant can visit
      pheromone_matrix: value of pheromone between nodes
      distance_matrix: the distance matrix of the nodes
      cost_function: a function to calculate the cost of a path
      max_load: max load for each ant
      demand: vertices demand
      alpha, beta, gamma, lam: algorithm parameters
      Q: queue to merge output data from processes

      route: the route path of the ant
      cost: cost of the route
      load: how much load has the ant
    """

    def __init__(self, current_node, unvisited_nodes, pheromone_matrix, distance_matrix, cost_function, max_load, demand, alpha, beta, gamma, lam, Q):
        super(Ant, self).__init__()
        self._current_node = current_node
        self._unvisited_nodes = unvisited_nodes[:]
        self._pheromone_matrix = pheromone_matrix
        self._distance_matrix = distance_matrix
        self._cost_function = cost_function
        self._max_load = max_load
        self._demand = demand
        self._alpha = alpha
        self._beta = beta
        self._gamma = gamma
        self._lam = lam
        self._Q = Q

        self._route = []
        self._routes = None
        self._cost = 0.0
        self._load = 0

        # add nest to route
        self._add_node_to_route(self._current_node)

    def reset_ant(self, current_node, unvisited_nodes, pheromone_matrix):
        """
        Reset an ant for a next pass
        """
        self.__init__(self._current_node, unvisited_nodes, pheromone_matrix, self._distance_matrix, self._cost_function,
                      self._max_load, self._demand, self._alpha, self._beta, self._gamma, self._lam, self._Q)
        self._routes = None

    def run(self):
        """
        Start the journey of an ant
        It returns to the nest when full until all the nodes are visited
        """
        count_nodes = len(self._unvisited_nodes)

        while self._unvisited_nodes:
            to_node = self._find_best_route()

            # if the ant is in the nest and the next node is a deficit node, starts with a load that allows to satisfy the demand of to_node
            if(self._demand[to_node.id] < 0 and self._current_node == self._route[0]):
                self._load = self._max_load

            # if count_nodes is less than zero we can't find a solution
            # the ant tried to visit all the unvisited states without success
            if(count_nodes < 0):
                return {"route": None,
                        "cost": None}

            if (self._load + self._demand[to_node.id] > self._max_load or self._load + self._demand[to_node.id] < 0):
                # returns to the deposit since the ant is full or it hasn't enough food
                if(self._current_node != self._route[0]):
                    self._return_to_nest()

                # checks if there isn't any solution
                count_nodes -= 1
                continue

            # if the cost of the the trip from the current node to the to_node is greater
            # than the trip from the current node and the nest plus the trip from the nest
            # to the to_node, then return to the nest
            if (self._cost_function(self._current_node, to_node) > self._cost_function(self._current_node, self._route[0]) + self._cost_function(self._route[0], to_node)):
                self._return_to_nest()
                continue

            self._step_route(self._current_node, to_node)

        # if we finished the unvisited nodes we should return to the deposit,
        # but only if we are not in the deposit
        if self._route[-1] is not self._route[0]:
            self._return_to_nest()

        self._routes = utils.split_route(self._route)

        self._cost = self._route_optimization()

        self._Q.put({"route": self._routes,
                     "cost": self._cost})

        # return {"route": self._route,
        #        "cost": self._cost}

    def _return_to_nest(self):
        """
        Return the ant to the nest
        """
        self._unvisited_nodes.extend([self._route[0]])
        self._step_route(self._current_node, self._route[0])
        self._load = 0

    def _step_route(self, from_node, to_node):
        """
          Do a new step on the route
        """
        self._add_node_to_route(to_node)
        self._update_cost(from_node, to_node)
        self._load += self._demand[to_node.id]
        self._current_node = to_node

    def _add_node_to_route(self, node):
        """
          Add new node to route and remove it from unvisited nodes
        """
        self._route.extend([node])
        self._unvisited_nodes.remove(node)

    def _update_cost(self, from_node, to_node):
        """
          Update cost to reach a new node
        """
        self._cost += self._cost_function(from_node, to_node)

    def _find_best_route(self):
        """
          Find the best route according to the probability of each node
        """
        probability_list = dict()

        for node in self._unvisited_nodes:
            probability = self._calculate_probability(node)
            probability_list[node] = probability

        # select at random between the 3 nodes with max probability
        to_node = random.choice(
            list(nlargest(2, probability_list, key=probability_list.__getitem__)))

        return to_node

        # return min(probability_list, key=probability_list.__getitem__)

    def _route_optimization(self):
        """
        Call of methods to further optimize the route
        """
        cost = 0.0

        self._inverse_optimization()
        self._two_opt()

        for route in self._routes:
            cost += utils.calculate_route_cost(self._cost_function, route)

        return cost

    def _inverse_optimization(self):
        """
        Check if the cost of an inverted route is lower than the cost of the non-inverted route
        """

        for i, route in enumerate(self._routes):
            inverted_route = list(reversed(route))

            check = utils.check_demand(inverted_route, self._demand, self._max_load)

            # consider only route with valid demand and which are not composed by a cycle of only one non-nest node
            if check and len(inverted_route) > 3:
                route_cost = utils.calculate_route_cost(self._cost_function, route)
                inverted_route_cost = utils.calculate_route_cost(
                    self._cost_function, inverted_route)

                if (inverted_route_cost < route_cost):
                    self._routes[i] = inverted_route

    def remove_depot(self, route):
        route = [node for node in route if node.id != 0]
        return route

    def opt_swap(self, route, i, k):
        route_to_i = route[:i]
        route_to_k = list(reversed(route[i:k]))
        route_to_end = route[k:]

        return route_to_i + route_to_k + route_to_end

    def _two_opt(self):
        new_route_cost = 0.0
        new_best_route = []

        for k, route in enumerate(self._routes):
            new_route = self.remove_depot(route)
            current_cost = utils.calculate_route_cost(self._cost_function, route)
            old_route_cost = current_cost

            for i in range(len(new_route)):
                for j in range(i+1, len(new_route)):
                    new_route = self.opt_swap(new_route, i, j)

                    if utils.check_demand(new_route, self._demand, self._max_load):
                        new_route_cost = utils.calculate_route_cost(self._cost_function, new_route)

                        new_route_cost += self._distance_matrix[route[0].id][new_route[0].id] + \
                            self._distance_matrix[new_route[len(
                                new_route)-1].id][route[0].id]

                        if new_route_cost < current_cost:
                            current_cost = new_route_cost
                            new_best_route = new_route

            if old_route_cost > current_cost:
                new_best_route.insert(0, route[0])
                new_best_route.append(route[0])
                self._routes[k] = new_best_route

    def _calculate_probability(self, node):
        """
        Calculate probability of a route
        """

        numerator = utils.calculate_numerator(self._pheromone_matrix, self._distance_matrix, self._current_node,
                                        node, self._load, self._max_load, self._demand, self._alpha, self._beta, self._gamma, self._lam)
        denominator = utils.calculate_denominator(self._unvisited_nodes, self._pheromone_matrix, self._distance_matrix, self._current_node,
                                            node, self._load, self._max_load, self._demand, self._alpha, self._beta, self._gamma, self._lam)
        probability = utils.calculate_probability(numerator, denominator)

        return probability
