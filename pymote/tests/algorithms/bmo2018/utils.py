from itertools import product
from networkx import Graph, minimum_spanning_tree
from numpy import array, pi, sin, cos, dot, sqrt
from pymote import Network, NetworkGenerator


def get_tree_network(n):
    net_gen = NetworkGenerator(n, commRange=0)
    net = net_gen.generate_random_network()
    for (n1, p1), (n2, p2) in product(net.pos.items(), net.pos.items()):
        Graph.add_edge(net, n1, n2, {
            'weight': sqrt(dot(p1-p2, p1-p2))
        })
    graph_tree = minimum_spanning_tree(net, 'weight')
    net.adj = graph_tree.adj
    return net


def get_complete_network(n):
    net = get_ring(n, 200)
    for n1, n2 in product(net.nodes(), net.nodes()):
        if n1 != n2:
            Graph.add_edge(net, n1, n2)
    return net


def get_line_network(n):
    net = get_ring(n, 200)
    for n1, n2 in zip(net.nodes(), net.nodes()[1:]):
        Graph.add_edge(net, n1, n2)
    return net


def get_ring_network(n, r=200, center=None):
    net = get_ring(n, r, center)
    for n1, n2 in zip(net.nodes(), net.nodes()[1:]+net.nodes()[:1]):
        Graph.add_edge(net, n1, n2)
    return net


def get_ring(n, r, center=None):
    net = Network()
    center = center or array(net.environment.im.shape)/2
    alpha = 2*pi/n
    for i in range(n):
        theta = i*alpha+1
        pos = array([cos(theta), sin(theta)])*r + center
        net.add_node(pos=pos, commRange=0)
    return net


def status_stat(klass, net, do_print=False):
    """ Prints number of nodes in certain status. For status in which there
    are minority of nodes, print node ids also. """
    statuses_counter = dict(
        zip(klass.STATUS.keys(), [[] for i in range(len(klass.STATUS))])
    )
    for node in net.nodes():
        statuses_counter[node.status].append(node)
    if do_print:
        for status, nodes in statuses_counter.items():
            print "%s: %d %s" % (
                status,
                len(nodes),
                str([n for n in nodes])
                if len(nodes) > 0 and len(nodes)/float(len(net.nodes())) < 0.2
                else ''
            )
    return statuses_counter
