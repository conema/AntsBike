from math import log
from numpy import nextafter, inf


def calculate_tau(pheromone_matrix, current_node, node, alpha):
    tau = pheromone_matrix[current_node.id][node.id]**alpha

    if tau == 0.0:
        tau = nextafter(0.1, inf)

    return tau


def calculate_eta(distance_matrix, current_node, node, beta):
    return (1/distance_matrix[current_node.id][node.id]) ** beta


def calculate_mi(distance_matrix, current_node, node, gamma):
    mi = (distance_matrix[current_node.id][0] + distance_matrix[0]
          [node.id] - distance_matrix[current_node.id][node.id]) ** gamma

    if mi == 0.0:
        mi = nextafter(0.1, inf)
    return mi


def calculate_k(load, demand, max_load, node, lam):
    return ((load + abs(demand[node.id])) / max_load) ** lam


def calculate_numerator(pheromone_matrix, distance_matrix, current_node, node, load, max_load, demand, alpha, beta, gamma, lam):
    """
    Calculate numerator to compute the probability of a route
    """
    tau = calculate_tau(pheromone_matrix, current_node, node, alpha)
    eta = calculate_eta(distance_matrix, current_node, node, beta)
    mi = calculate_mi(distance_matrix, current_node, node, gamma)
    k = calculate_k(load, demand, max_load, node, lam)

    return 10**(log(tau, 10)+log(eta, 10)+log(mi, 10)+log(k, 10))


def calculate_denominator(unvisited_nodes, pheromone_matrix, distance_matrix, current_node, node, load, max_load, demand, alpha, beta, gamma, lam):
    """
    Calculate denominator to compute the probability of a route
    """
    sum = 0.0

    for node in unvisited_nodes:
        tau = calculate_tau(pheromone_matrix, current_node, node, alpha)
        eta = calculate_eta(distance_matrix, current_node, node, beta)
        mi = calculate_mi(distance_matrix, current_node, node, gamma)
        k = calculate_k(load, demand, max_load, node, lam)

        sum += 10**(log(tau, 10) + log(eta, 10) + log(mi, 10) + log(k, 10))

    return sum


def calculate_probability(numerator, denominator):
    if denominator == 0.0:
        denominator = nextafter(0.1, inf)

    return numerator/denominator


def split_route(route):
    """
    Split a full route into single nest to nest subroute
    """
    routes = []
    i = -1

    for node in route:
        if node.id == 0:
            # start a new subroute in position i
            if i != -1:
                # close the old subroute
                routes[i].append(route[0])

            # start the new subroute
            routes.append([node])
            i += 1
        else:
            # add node to the i-subroute
            routes[i].append(node)

    # return all the subroute except for the last one, which is composed only by the nest (node 0)
    return routes[:-1]


def calculate_route_cost(cost_function, route):
    """
    Calculate cost of a single subroute
    """
    cost = 0.0

    for node, next_node in zip(route, route[1:]):
        cost += cost_function(node, next_node)

    return cost


def check_demand(route, demand, max_load):
    """
    Check if the load of the ant doesn't exceed max_load or isn't below zero
    """
    sum = 0

    for node in route:
        sum += demand[node.id]

        if sum > max_load or sum < 0:
            return False

    return True
