from simulator import Simulator

def main():
    print("=== Meshtastic Network Simulator ===")
    num_nodes = int(input("Enter number of nodes (10-100): "))
    num_messages = int(input("Enter number of messages to send: "))
    mode = input("Run messages (1) one-by-one or (2) simultaneously? [1/2]: ")
    simultaneous = (mode.strip() == "2")

    sim = Simulator(num_nodes=num_nodes, simultaneous=simultaneous)
    sim.setup_messages(num_messages=num_messages)
    sim.run_gui()

if __name__ == "__main__":
    main()
