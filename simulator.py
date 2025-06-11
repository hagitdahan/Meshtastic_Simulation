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

        # Prepare to detect collisions
        message_hits = {}  # node_id -> count of incoming messages

        # First pass to count hits per node
        for msg in self.message_manager.get_active_messages():
            if time < msg.timestamp or msg.delivered or msg.expired:
                continue
            seen_nodes = self.message_states[msg.message_id]
            for node in seen_nodes:
                for neighbor in graph.neighbors(node):
                    if neighbor not in seen_nodes:
                        message_hits[neighbor] = message_hits.get(neighbor, 0) + 1

        # Detect collisions
        self.blocked_nodes = {node_id for node_id, count in message_hits.items() if count > 1}

        # Second pass to spread messages
        for msg in self.message_manager.get_active_messages():
            if time < msg.timestamp or msg.delivered or msg.expired:
                continue

            seen_nodes = self.message_states[msg.message_id]
            new_seen = set()

            for node in seen_nodes:
                if node in self.blocked_nodes:
                    continue  # skip spreading from collided node
                for neighbor in graph.neighbors(node):
                    if neighbor in self.blocked_nodes:
                        continue  # don't forward to a collided node
                    if neighbor not in seen_nodes:
                        new_seen.add(neighbor)
                        self.message_edges[msg.message_id].append((node, neighbor))
                    if neighbor == msg.destination:
                        self.message_manager.mark_delivered(msg)

            seen_nodes.update(new_seen)


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
            color = "lightblue"

            if node_id in self.blocked_nodes:
                color = "pink"
            else:
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

        # Separate messages by status
        active_messages = []
        completed_messages = []

        for m in self.message_manager.messages:
            if m.delivered or m.expired:
                completed_messages.append(m)
            else:
                active_messages.append(m)

        # Create message descriptions
        active_descriptions = []
        completed_descriptions = []

        # Active messages (blue text)
        for m in active_messages:
            if m.timestamp > current_time:
                status = "Waiting"
            else:
                status = "Active"
            line = f"#{m.message_id}: {m.source}→{m.destination} | TTL={m.ttl} | T={m.timestamp} | {status}"
            active_descriptions.append(line)

        # Completed messages (green for delivered, red for expired)
        for m in completed_messages:
            if m.delivered:
                status = "✓ Delivered"
            else:
                status = "✗ Expired"
            line = f"#{m.message_id}: {m.source}→{m.destination} | TTL={m.ttl} | T={m.timestamp} | {status}"
            completed_descriptions.append(line)

        # Clear old texts
        for txt in self.fig.texts:
            txt.set_visible(False)

        # Display active messages
        if active_descriptions:
            # Separate waiting and truly active messages
            waiting_msgs = [line for line in active_descriptions if "Waiting" in line]
            active_msgs = [line for line in active_descriptions if "Active" in line]
           
            y_pos = 0.7
           
            # Show waiting messages in black
            if waiting_msgs:
                self.fig.text(0.78, y_pos, "Waiting Messages:\n" + "\n".join(waiting_msgs),
                            fontsize=9, va='top', ha='left', transform=self.fig.transFigure, color='black')
                y_pos -= 0.15
           
            # Show active messages in blue
            if active_msgs:
                self.fig.text(0.78, y_pos, "Active Messages:\n" + "\n".join(active_msgs),
                            fontsize=9, va='top', ha='left', transform=self.fig.transFigure, color='blue')

        # Display completed messages
        if completed_descriptions:
            # Separate delivered and expired for different colors
            delivered_msgs = [line for line in completed_descriptions if "✓" in line]
            expired_msgs = [line for line in completed_descriptions if "✗" in line]
           
            y_pos = 0.4
            if delivered_msgs:
                self.fig.text(0.78, y_pos, "Completed Successfully:\n" + "\n".join(delivered_msgs),
                            fontsize=9, va='top', ha='left', transform=self.fig.transFigure, color='green')
                y_pos -= 0.15
           
            if expired_msgs:
                self.fig.text(0.78, y_pos, "Failed/Expired:\n" + "\n".join(expired_msgs),
                            fontsize=9, va='top', ha='left', transform=self.fig.transFigure, color='red')
        self.ax.set_title(f"Time: {current_time}")
        plt.pause(0.01)

        # Only set wait flag — don't close yet
        if all((msg.delivered or msg.expired) for msg in self.message_manager.messages):
            self.waiting_for_final_enter = True
