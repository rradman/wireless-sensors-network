# -*- coding: utf-8 -*-
import logging
import networkx as nx
import unittest
from .utils import get_tree_network, get_line_network, get_complete_network, \
    get_ring_network, status_stat
from itertools import combinations
from pymote import write_pickle
from pymote.algorithms.bmo2018 import routing
from pymote.network import Network
from pymote.networkgenerator import NetworkGenerator
from pymote.simulation import Simulation
from random import randint


class RoutingRunnerBase(object):

    def setUp(self):
        pass

    def test_tree(self):
        self.net = get_tree_network(30)
        self.run_test()

    def test_line_small(self):
        self.net = get_line_network(2)
        self.run_test()

    def test_line(self):
        self.net = get_line_network(10)
        self.run_test()

    def test_binarytree(self):
        self.net = Network()
        self.net.add_node(pos=(300, 300), commRange=101)  # root
        self.net.add_node(pos=(300, 400), commRange=101)
        self.net.add_node(pos=(399, 400), commRange=100)
        self.net.add_node(pos=(300, 498), commRange=99)
        self.net.add_node(pos=(399, 303), commRange=98)
        self.net.add_node(pos=(495, 400), commRange=97)
        self.net.add_node(pos=(205, 498), commRange=96)
        self.net.add_node(pos=(300, 592), commRange=95)
        self.net.add_node(pos=(207, 300), commRange=94)
        self.net.add_node(pos=(207, 208), commRange=93)
        self.net.add_node(pos=(116, 300), commRange=92)
        self.net.add_node(pos=(116, 390), commRange=91)
        self.net.add_node(pos=(27, 300), commRange=90)
        self.net.add_node(pos=(119, 208), commRange=89)
        self.net.add_node(pos=(207, 121), commRange=88)
        self.run_test()

    def test_unique(self):
        self.net = Network()
        self.net.add_node(pos=(300, 0), commRange=101)
        self.net.add_node(pos=(300, 100), commRange=101)
        self.net.add_node(pos=(300, 200), commRange=150)
        self.net.add_node(pos=(200, 300), commRange=150)
        self.net.add_node(pos=(400, 300), commRange=150)
        self.net.add_node(pos=(300, 300), commRange=101)
        self.net.add_node(pos=(300, 400), commRange=150)
        self.net.add_node(pos=(300, 500), commRange=101)
        self.net.add_node(pos=(300, 599), commRange=101)
        self.net.add_node(pos=(100, 300), commRange=101)
        self.net.add_node(pos=(0, 300), commRange=101)
        self.net.add_node(pos=(500, 300), commRange=101)
        self.net.add_node(pos=(599, 300), commRange=101)
        self.run_test()

    def test_complete(self):
        self.net = get_complete_network(10)
        self.run_test()

    def test_ring(self):
        self.net = get_ring_network(10, 200, (300, 300))
        self.run_test()

    def test_mesh(self):
        net_gen = NetworkGenerator(20)
        self.net = net_gen.generate_homogeneous_network(0)
        self.run_test()

    def test_random_small(self):
        net_gen = NetworkGenerator(5, comm_range=600)
        self.net = net_gen.generate_random_network()
        self.run_test()

    def test_random_medium(self):
        net_gen = NetworkGenerator(10, comm_range=400)
        self.net = net_gen.generate_random_network()
        self.run_test()

    def test_random_large(self):
        net_gen = NetworkGenerator(20)
        self.net = net_gen.generate_random_network()
        self.run_test()

    def setup_weights(self):
        edges = self.net.edges(data=True)
        max_weight = 100 if self.weighted else 1
        weights = map(lambda e: randint(1, max_weight), edges)
        for weight, (u, v, data) in zip(weights, edges):
            data[self.weight_key] = weight

    def check_statuses(self):
        statuses_counter = status_stat(self.algorithm, self.net)
        self.assertEqual(
            len(statuses_counter["DONE"]),
            len(self.net.nodes()) - 1
        )
        self.assertEqual(len(statuses_counter["INITIATOR"]), 1)

    def check_routing_table(self):
        statuses_counter = status_stat(self.algorithm, self.net)
        source = statuses_counter["INITIATOR"][0]
        for node in self.net.nodes():
            if node == source:
                continue
            shortest_paths = nx.all_shortest_paths(
                self.net, source=source, target=node, weight=self.weight_key
            )
            # take all shortest paths starting nodes
            sp_starts = map(lambda sp: sp[1], shortest_paths)
            # assert that source routing table has one of them as next hop
            self.assertTrue(
                source.memory[self.routing_table_key][node] in sp_starts
            )

    def check_routing_tables(self):
        for (n1, n2) in combinations(self.net.nodes(), 2):
            shortest_path = []
            n = n1
            # while current node n is not target node n2
            while n != n2:
                shortest_path.append(n)
                n = n.memory[self.routing_table_key][n2]
                # routing table value can sometimes be a list of nodes
                if isinstance(n, list):
                    n = n[0]
            # lastly add target node n2 to shortest path
            shortest_path.append(n2)
            self.assertTrue(shortest_path in nx.all_shortest_paths(
                self.net, source=n1, target=n2, weight=self.weight_key
            ))

    def check(self):
        pass

    def run_test(self):
        self.weight_key = 'weight'
        self.setup_weights()
        self.routing_table_key = 'RoutingTable'
        self.net.algorithms = ((self.algorithm, {
            'routingTableKey': self.routing_table_key
        }), )
        # Write network to disk to be able to debug in simulator
        write_pickle(self.net, 'net.npc.gz')
        self.sim = Simulation(self.net, logLevel=logging.ERROR)
        self.sim.run()
        self.check()


# class WeightedRoutingRunner(unittest.TestCase, RoutingRunnerBase):

#     def setUp(self):
#         self.algorithm = routing.PTConstruction
#         self.weighted = True

#     def check(self):
#         self.check_statuses()
#         self.check_routing_table()


class WeightedRoutingsRunner(unittest.TestCase, RoutingRunnerBase):

    def setUp(self):
        self.algorithm = routing.PTAll
        self.weighted = True

    def check_statuses(self):
        statuses_counter = status_stat(self.algorithm, self.net)
        self.assertEqual(
            len(statuses_counter["DFT_DONE"]),
            len(self.net.nodes())
        )

    def check(self):
        self.check_statuses()
        self.check_routing_tables()
