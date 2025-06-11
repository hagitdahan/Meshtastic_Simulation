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
    def __init__(self, num_nodes, space_size=200):
        self.num_nodes = num_nodes
        self.nodes = {}  # node_id -> Node
        self.graph = nx.Graph()
        self.space_size = space_size
        self.communication_radius = 0
        self.target_avg_neighbors = 4
        self._place_nodes()
        self.analyze_distribution()

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

        # Adaptive minimum distance - smaller for more nodes
        base_distance = self.space_size / math.sqrt(self.num_nodes * 2.5)
        min_distance = max(2, base_distance)
        
        max_attempts = self.num_nodes * 800
        placed = 0
        attempts = 0
        positions = []

        print(f"Placing {self.num_nodes} nodes in {self.space_size}x{self.space_size} space...")
        print(f"Minimum distance: {min_distance:.2f}")

        # Start with Poisson disk sampling approach for better distribution
        while placed < self.num_nodes and attempts < max_attempts:
            
            if attempts < max_attempts // 4:
                # Phase 1: Random with rejection sampling
                x = random.uniform(min_distance, self.space_size - min_distance)
                y = random.uniform(min_distance, self.space_size - min_distance)
                
            elif attempts < max_attempts // 2:
                # Phase 2: Hexagonal grid with noise for better packing
                rows = int(math.ceil(math.sqrt(self.num_nodes)))
                cols = int(math.ceil(self.num_nodes / rows))
                
                row = placed // cols
                col = placed % cols
                
                # Hexagonal offset for every other row
                offset_x = (min_distance * 0.8) if row % 2 == 1 else 0
                
                spacing_x = (self.space_size - 2 * min_distance) / max(1, cols - 1)
                spacing_y = (self.space_size - 2 * min_distance) / max(1, rows - 1)
                
                base_x = min_distance + col * spacing_x + offset_x
                base_y = min_distance + row * spacing_y
                
                # Add controlled randomness
                noise = min_distance * 0.3
                x = base_x + random.uniform(-noise, noise)
                y = base_y + random.uniform(-noise, noise)
                
                # Keep within bounds
                x = max(min_distance, min(self.space_size - min_distance, x))
                y = max(min_distance, min(self.space_size - min_distance, y))
                
            else:
                # Phase 3: Force-based placement - find largest empty area
                best_x, best_y = 0, 0
                max_min_dist = 0
                
                # Try multiple random points and pick the one farthest from existing nodes
                for _ in range(50):
                    test_x = random.uniform(min_distance, self.space_size - min_distance)
                    test_y = random.uniform(min_distance, self.space_size - min_distance)
                    
                    # Find minimum distance to existing nodes
                    min_dist_to_existing = float('inf')
                    for ex_x, ex_y in positions:
                        dist = math.dist((test_x, test_y), (ex_x, ex_y))
                        min_dist_to_existing = min(min_dist_to_existing, dist)
                    
                    if min_dist_to_existing > max_min_dist:
                        max_min_dist = min_dist_to_existing
                        best_x, best_y = test_x, test_y
                
                x, y = best_x, best_y

            # Check distance constraint
            too_close = any(
                math.dist((x, y), (pos_x, pos_y)) < min_distance
                for pos_x, pos_y in positions
            )
            
            if too_close:
                attempts += 1
                # Gradually reduce min_distance if we're having trouble
                if attempts > max_attempts * 0.75:
                    min_distance *= 0.98
                continue

            # Place the node
            node = Node(placed, x, y)
            self.nodes[placed] = node
            self.graph.add_node(placed, pos=(x, y))
            positions.append((x, y))
            placed += 1
            attempts += 1

            # Progress indicator
            if self.num_nodes > 30 and placed % 25 == 0:
                print(f"  Placed {placed}/{self.num_nodes} nodes... (attempts: {attempts})")

        if placed < self.num_nodes:
            print(f"Warning: Only placed {placed}/{self.num_nodes} nodes after {attempts} attempts.")
            self.num_nodes = placed

        print(f"Successfully placed {placed} nodes with average separation: {min_distance:.2f}")
        
        self.communication_radius = self._calculate_communication_radius(target_avg=4)
        self._create_edges()

    def analyze_distribution(self):
        """Analyze and print node distribution quality"""
        if len(self.nodes) < 2:
            return
        
        positions = [(node.x, node.y) for node in self.nodes.values()]
        
        # Calculate all pairwise distances
        distances = []
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dist = math.dist(positions[i], positions[j])
                distances.append(dist)
        
        # Statistics
        min_dist = min(distances)
        max_dist = max(distances)
        avg_dist = sum(distances) / len(distances)
        
        # Calculate distribution uniformity (coefficient of variation)
        variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)
        std_dev = math.sqrt(variance)
        cv = std_dev / avg_dist if avg_dist > 0 else 0
        
        # Divide space into grid and count nodes per cell
        grid_size = 5
        cell_width = self.space_size / grid_size
        cell_counts = {}
        
        for x, y in positions:
            cell_x = int(x // cell_width)
            cell_y = int(y // cell_width)
            cell_key = (cell_x, cell_y)
            cell_counts[cell_key] = cell_counts.get(cell_key, 0) + 1
        
        # Expected nodes per cell for uniform distribution
        expected_per_cell = len(positions) / (grid_size * grid_size)
        
        print(f"\n=== DISTRIBUTION ANALYSIS ===")
        print(f"Nodes placed: {len(positions)}")
        print(f"Space size: {self.space_size}x{self.space_size}")
        print(f"Min distance: {min_dist:.2f}")
        print(f"Max distance: {max_dist:.2f}")
        print(f"Avg distance: {avg_dist:.2f}")
        print(f"Distance std dev: {std_dev:.2f}")
        print(f"Uniformity (lower is better): {cv:.3f}")
        print(f"Expected nodes per {grid_size}x{grid_size} cell: {expected_per_cell:.1f}")
        
        # Show cell distribution
        non_empty_cells = len([c for c in cell_counts.values() if c > 0])
        total_cells = grid_size * grid_size
        print(f"Occupied cells: {non_empty_cells}/{total_cells}")
        
        if cv < 0.5:
            print("✓ Good distribution")
        elif cv < 0.8:
            print("⚠ Moderate distribution")
        else:
            print("✗ Poor distribution - consider adjusting parameters")
        print("=" * 30)
    
    def _calculate_communication_radius(self, target_avg=4):
        if len(self.nodes) < 2:
            return self.space_size / 4
            
        dists = []
        node_list = list(self.nodes.values())
        
        # For large networks - sample for better performance
        if len(node_list) > 50:
            sample_size = 2000
            for _ in range(sample_size):
                i, j = random.sample(node_list, 2)
                dists.append(self._distance(i, j))
        else:
            # For small networks - full calculation
            for i in range(len(node_list)):
                for j in range(i + 1, len(node_list)):
                    dists.append(self._distance(node_list[i], node_list[j]))
        
        dists.sort()
        
        # Binary search for optimal radius
        min_r, max_r = min(dists), max(dists)
        
        for _ in range(15):
            mid_r = (min_r + max_r) / 2
            avg = self._average_neighbors(mid_r)
            
            if abs(avg - target_avg) < 0.3:
                return mid_r
            elif avg < target_avg:
                min_r = mid_r
            else:
                max_r = mid_r
                
        return (min_r + max_r) / 2

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