from simulator import Simulator

def main():
    print("=== Meshtastic Network Simulator ===")
    num_nodes = int(input("Enter number of nodes (10-100): "))
    num_messages = int(input("Enter number of messages to send: "))
    sim = Simulator(num_nodes=num_nodes)
    sim.setup_messages(num_messages=num_messages)
    sim.run_gui()

if __name__ == "__main__":
    main()
