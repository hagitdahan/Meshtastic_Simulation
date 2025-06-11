# network.py
import math
import random
import networkx as nx
import numpy as np

class Node:
    def __init__(self, node_id, x, y):
        self.id = node_id
        self.x = x
        self.y = y
        self.neighbors = set()  # Needed for the graph

    def add_neighbor(self, neighbor_id):
        self.neighbors.add(neighbor_id)

    def position(self):
        return (self.x, self.y)

    def distance_from(self, other_node):
        return ((self.x - other_node.x) ** 2 + (self.y - other_node.y) ** 2) ** 0.5

class Network:
    def __init__(self, num_nodes, space_size=100):
        self.num_nodes = num_nodes  # <-- this line is crucial
        self.nodes = {}  # node_id -> Node
        self.graph = nx.Graph()
        self.space_size = space_size
        self.communication_radius = 0
        self.target_avg_neighbors = 4
        self._place_nodes()

    def _distance(self, node1, node2):
        return math.hypot(node1.x - node2.x, node1.y - node2.y)

    def _get_radius(self):
        if self.communication_radius:
            return self.communication_radius
        area = self.space_size ** 2
        return math.sqrt((4 * area) / (math.pi * self.num_nodes))

    def _place_nodes(self):
        self.nodes.clear()
        self.graph.clear()

        min_distance = 0.15 * self.space_size
        max_attempts = self.num_nodes * 100
        placed = 0
        attempts = 0
        positions = []

        while placed < self.num_nodes and attempts < max_attempts:
            x = random.uniform(0, self.space_size)
            y = random.uniform(0, self.space_size)
            too_close = any(
                math.dist((x, y), (nx, ny)) < min_distance
                for nx, ny in positions
            )
            if too_close:
                attempts += 1
                continue

            node = Node(placed, x, y)
            self.nodes[placed] = node
            self.graph.add_node(placed, pos=(x, y))
            positions.append((x, y))
            placed += 1
            attempts += 1

        if placed < self.num_nodes:
            print(f"⚠ Warning: Only placed {placed}/{self.num_nodes} nodes after {attempts} attempts.")

        self.communication_radius = self._calculate_communication_radius(target_avg=4)
        self._create_edges()

    def _distance(self, node1, node2):
        return math.hypot(node1.x - node2.x, node1.y - node2.y)

    def _calculate_communication_radius(self, target_avg=4):
        dists = []
        for i in self.nodes:
            for j in self.nodes:
                if i != j:
                    dists.append(self._distance(self.nodes[i], self.nodes[j]))
        dists.sort()
        
        for r in np.linspace(min(dists), max(dists), 100):
            avg = self._average_neighbors(r)
            if avg >= target_avg:
                return r
        return max(dists)

    def _average_neighbors(self, radius):
        total = 0
        for i in self.nodes:
            neighbors = sum(
                1 for j in self.nodes
                if i != j and self._distance(self.nodes[i], self.nodes[j]) <= radius
            )
            total += neighbors
        return total / len(self.nodes) if self.nodes else 0

    def _create_edges(self):
        self.graph.clear_edges()
        for i in self.nodes:
            for j in self.nodes:
                if i != j:
                    if self._distance(self.nodes[i], self.nodes[j]) <= self.communication_radius:
                        self.graph.add_edge(i, j)
                        self.nodes[i].add_neighbor(j)

    def get_graph(self):
        return self.graph

    def get_positions(self):
        return {node_id: node.position() for node_id, node in self.nodes.items()}

    def get_radius(self):
        return self._get_radius()

    def get_diameter(self):
        if nx.is_connected(self.graph):
            return nx.diameter(self.graph)
        return -1
