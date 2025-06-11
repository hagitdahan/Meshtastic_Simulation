import matplotlib.pyplot as plt
from network import Network
from message import MessageManager
import networkx as nx

class Simulator:
    def __init__(self, num_nodes,routing_mode="flooding"):
        self.network = Network(num_nodes)
        self.message_manager = MessageManager()
        self.routing_mode = routing_mode
        self.message_states = {}
        self.message_edges = {}
        self.acknowledged = {}  
        self.fig, self.ax = plt.subplots(figsize=(16, 12))
        self.paused = True
        self.waiting_for_final_enter = False  # flag to wait for last ENTER
        self.blocked_nodes = set()  # nodes that had a collision


    def setup_messages(self, num_messages):
        node_ids = list(self.network.nodes.keys())
        self.message_manager.generate_random_pairs(num_messages, node_ids)
        for msg in self.message_manager.messages:
            self.message_states[msg.message_id] = set([msg.source])
            self.message_edges[msg.message_id] = []
            self.acknowledged[msg.message_id] = False  # not acknowledged yet

    def step(self):
        self.message_manager.advance_time()
        graph = self.network.get_graph()
        time = self.message_manager.current_time

        for msg in self.message_manager.get_active_messages():
            if time < msg.timestamp or msg.delivered or msg.expired:
                continue

            seen_nodes = self.message_states[msg.message_id]
            new_seen = set()

            for node in seen_nodes:
                if node in self.blocked_nodes:
                    continue  # Skip nodes that had a collision
                for neighbor in graph.neighbors(node):
                    if neighbor not in seen_nodes:
                        new_seen.add(neighbor)
                        self.message_edges[msg.message_id].append((node, neighbor))
                        if neighbor == msg.destination:
                            self.message_manager.mark_delivered(msg)

            seen_nodes.update(new_seen)
        self.blocked_nodes.clear() 

    def run_gui(self):
        self.visualize()

        def on_key(event):
            if event.key == 'enter':
                # Acknowledge all completed messages
                for msg in self.message_manager.messages:
                    if msg.delivered or msg.expired:
                        self.acknowledged[msg.message_id] = True

                if self.waiting_for_final_enter:
                    print("Simulation ended. Pressed ENTER after final message.")
                    plt.close('all')
                else:
                    self.step()
                    self.visualize()

        self.fig.canvas.mpl_connect('key_press_event', on_key)
        plt.show()

    def visualize(self):
        graph = self.network.get_graph()
        pos = self.network.get_positions()
        self.ax.clear()
        self.fig.subplots_adjust(right=0.75)
        current_time = self.message_manager.current_time

        # Track collisions
        message_hits = {}  # node_id → number of messages received this round

        for msg in self.message_manager.get_active_messages():
            if current_time >= msg.timestamp and not msg.delivered and not msg.expired:
                msg_id = msg.message_id
                for u, v in self.message_edges[msg_id]:
                    if v not in message_hits:
                        message_hits[v] = 0
                    message_hits[v] += 1
        
        for node_id, count in message_hits.items():
            if count > 1:
                self.blocked_nodes.add(node_id)


        # Node coloring
        colors = []
        for node_id in graph.nodes:
            color = "lightblue"   # Collision turns to pink
            if node_id in self.blocked_nodes:
                #print(f"number of {message_hits.get(node_id, 0)},node_id {node_id}")
                color = "pink"
        
            # Check if part of an active (not yet acknowledged) message
            for msg in self.message_manager.messages:
                if not self.acknowledged[msg.message_id] and msg.timestamp <= current_time:
                    if msg.source == node_id:
                        color = "green"
                    elif msg.destination == node_id:
                        color = "red"

            colors.append(color)

        # Draw base graph and colored nodes
        nx.draw_networkx_edges(graph, pos, ax=self.ax, alpha=0.3)
        nx.draw_networkx_nodes(graph, pos, node_color=colors, node_size=600, ax=self.ax)
        nx.draw_networkx_labels(graph, pos, ax=self.ax)

        # Draw message paths
        cmap = ["blue", "purple", "orange", "brown", "darkgreen", "black", "cyan"]
        for idx, (msg_id, edges) in enumerate(self.message_edges.items()):
            if not self.acknowledged.get(msg_id, False):
                if idx < len(cmap):
                    nx.draw_networkx_edges(graph, pos, edgelist=edges, width=2, edge_color=cmap[idx], ax=self.ax)

        # Right-side message panel
        descriptions = []
        for m in self.message_manager.messages:
            if m.delivered:
                status = "Delivered"
            elif m.expired:
                status = "Expired"
            elif m.timestamp > current_time:
                status = "Waiting"
            else:
                status = "Active"
            line = f"#{m.message_id}: {m.source}→{m.destination} | TTL={m.ttl} | T={m.timestamp} | {status}"
            descriptions.append(line)

        # Clear old texts
        for txt in self.fig.texts:
            txt.set_visible(False)
        self.fig.text(0.78, 0.5, "\n\n".join(descriptions), fontsize=10, va='center', ha='left', transform=self.fig.transFigure)

        self.ax.set_title(f"Time: {current_time}")
        plt.pause(0.01)

        # Only set wait flag — don't close yet
        if all((msg.delivered or msg.expired) for msg in self.message_manager.messages):
            self.waiting_for_final_enter = True
