import random
import matplotlib.pyplot as plt
import networkx as nx
import heapq
from matplotlib.animation import FuncAnimation

class SensorNode:
    def __init__(self, node_id, energy, data, position):
        self.node_id = node_id
        self.energy = energy
        self.data = data
        self.position = position

    def is_alive(self):
        return self.energy > 0

    def harvest_energy(self):
        harvested_energy = random.uniform(0, 5)
        self.energy += harvested_energy
        print(f"Node {self.node_id} harvested {harvested_energy:.2f} energy.")

    def collect_data(self):
        if self.is_alive():
            collected_data = random.uniform(0, 10)
            self.data += collected_data
            print(f"Node {self.node_id} collected {collected_data:.2f} data.")
            return collected_data
        return 0

    def encrypt_data(self, data):
        encrypted_data = data * 1.1  # Simulated encryption
        print(f"Node {self.node_id} encrypted data: {encrypted_data:.2f}.")
        return encrypted_data

    def transmit_data(self, data, path):
        if self.is_alive() and self.energy > 0:
            energy_consumed = len(path) + (data / 10)  # Consume energy based on the length of the path and amount of data
            if self.energy >= energy_consumed:
                self.energy -= energy_consumed
                print(f"Node {self.node_id} transmitted {data:.2f} to {path[-1]} via path {path}.")
                return True
            else:
                print(f"Node {self.node_id} has insufficient energy to transmit.")
        return False


class ProxyBackend:
    def process_data(self, data):
        processed_data = data * 0.9  # Simulated data processing
        print(f"Processed data: {processed_data:.2f}.")
        return processed_data


class WBAN:
    def __init__(self, nodes_positions, base_station_position, node_energies):
        self.nodes = []
        self.proxy = ProxyBackend()
        self.transmission_paths = []
        self.energy_history = {}

        # Initialize nodes with user-defined positions and energy levels
        for i, position in enumerate(nodes_positions):
            node = SensorNode(f'Node {i}', energy=node_energies[i], data=0, position=position)
            self.nodes.append(node)
            self.energy_history[node.node_id] = []  # Initialize energy history for each node

        # Create the base station
        self.base_station = SensorNode("Base Station", 100, 0, base_station_position)

    def link_cost(self, node1, node2):
        """Calculate the link cost based on the energy levels of the nodes."""
        distance = ((node1.position[0] - node2.position[0]) ** 2 +
                     (node1.position[1] - node2.position[1]) ** 2) ** 0.5
        # Prevent division by zero by returning a large cost if either node's energy is zero
        if node1.energy == 0 or node2.energy == 0:
            return float('inf')
        return distance / min(node1.energy, node2.energy)  # Example cost function

    def dijkstra(self, start_node_id):
        graph = {node.node_id: [] for node in self.nodes}
        graph[self.base_station.node_id] = []

        for node in self.nodes:
            for other_node in self.nodes:
                if node.node_id != other_node.node_id:
                    cost = self.link_cost(node, other_node)
                    graph[node.node_id].append((other_node.node_id, cost))
                    graph[other_node.node_id].append((node.node_id, cost))  # Bidirectional edges
                # Add the base station edges
                cost_to_bs = self.link_cost(node, self.base_station)
                graph[node.node_id].append((self.base_station.node_id, cost_to_bs))

        # Dijkstra's algorithm
        queue = [(0, start_node_id)]  # (cost, node_id)
        distances = {node.node_id: float('inf') for node in self.nodes}
        distances[start_node_id] = 0
        distances[self.base_station.node_id] = float('inf')  # Initialize base station distance
        shortest_paths = {node.node_id: [] for node in self.nodes}
        visited = set()

        while queue:
            current_distance, current_node = heapq.heappop(queue)
            visited.add(current_node)

            for neighbor, weight in graph[current_node]:
                if neighbor in visited:
                    continue

                distance = current_distance + weight

                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    shortest_paths[neighbor] = shortest_paths[current_node] + [current_node]
                    heapq.heappush(queue, (distance, neighbor))

        return shortest_paths

    def simulate(self, rounds):
        for r in range(rounds):
            print(f"\nRound {r + 1}")
            for node in self.nodes:
                if node.is_alive():
                    node.harvest_energy()  # Harvest energy periodically
                    data = node.collect_data()
                    if data > 0:
                        processed_data = self.proxy.process_data(data)
                        encrypted_data = node.encrypt_data(processed_data)

                        # Find shortest path to the base station
                        shortest_paths = self.dijkstra(node.node_id)
                        path_to_bs = shortest_paths[self.base_station.node_id] + [self.base_station.node_id]

                        if node.transmit_data(encrypted_data, path_to_bs):
                            self.transmission_paths.append((node.node_id, path_to_bs))  # Store transmission path
                    else:
                        print(f"Node {node.node_id} has no energy to collect data.")

                    # Simulate node failure based on energy level
                    if node.energy < 5:  # Example threshold
                        print(f"Node {node.node_id} has failed due to low energy.")
                        node.energy = 0  # Mark node as failed
                else:
                    print(f"Node {node.node_id} is dead.")

                # Store the current energy level for each node
                self.energy_history[node.node_id].append(node.energy)

            # Move nodes randomly after each round
            for node in self.nodes:
                if node.is_alive():
                    node.position = (random.uniform(0, 10), random.uniform(0, 10))  # Randomly reposition nodes

        self.animate_data_transmission()

    def animate_data_transmission(self):
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.set_title("Data Transmission Animation")
        ax.set_xlabel("X Position")
        ax.set_ylabel("Y Position")

        # Plot nodes
        for node in self.nodes:
            color = 'red' if node.is_alive() else 'gray'  # Gray for dead nodes
            ax.scatter(node.position[0], node.position[1], c=color, s=100)
            ax.text(node.position[0], node.position[1], node.node_id, fontsize=12, ha='right')

        # Plot the base station
        ax.scatter(self.base_station.position[0], self.base_station.position[1], c='blue', s=200, marker='x')
        ax.text(self.base_station.position[0], self.base_station.position[1], "Base Station", fontsize=12, ha='right')

        # Create an empty line for the animation
        line, = ax.plot([], [], 'g-', linewidth=2)

        def init():
            line.set_data([], [])
            return line,

        def update(frame):
            if frame < len(self.transmission_paths):
                start, path = self.transmission_paths[frame]
                path_positions = []
                for node_id in path:
                    if node_id == "Base Station":
                        path_positions.append(self.base_station.position)  # Get base station position
                    else:
                        path_positions.append(self.nodes[int(node_id.split()[1])].position)  # Extract node position
                x_data, y_data = zip(*path_positions)
                line.set_data(x_data, y_data)
            return line,

        ani = FuncAnimation(fig, update, frames=len(self.transmission_paths), init_func=init, blit=True, repeat=False)
        plt.show()

    def plot_energy_levels(self):
        plt.figure(figsize=(12, 6))
        for node_id, energies in self.energy_history.items():
            plt.plot(energies, label=node_id)
        plt.title("Energy Levels of Nodes Over Time")
        plt.xlabel("Rounds")
        plt.ylabel("Energy Level")
        plt.legend()
        plt.grid()
        plt.show()


def get_node_positions_and_energy(num_nodes):
    """Function to allow user to place nodes and assign energy levels on a plot."""
    node_positions = []
    node_energies = []

    def onclick(event):
        if event.xdata is not None and event.ydata is not None:
            node_positions.append((event.xdata, event.ydata))
            plt.scatter(event.xdata, event.ydata, c='red', s=100)
            plt.draw()

    def on_key(event):
        if event.key == 'enter':
            plt.close()

    fig, ax = plt.subplots()
    ax.set_title("Click to place nodes. Press Enter when done.")
    plt.xlim(0, 10)
    plt.ylim(0, 10)
    cid_click = fig.canvas.mpl_connect('button_press_event', onclick)
    cid_key = fig.canvas.mpl_connect('key_press_event', on_key)

    plt.show()

    for i in range(num_nodes):
        energy = random.uniform(5, 20)  # Random energy between 5 and 20
        node_energies.append(energy)

    return node_positions, node_energies


if __name__ == "__main__":
    try:
        num_nodes = int(input("Enter the number of sensor nodes: "))  # Get the number of sensor nodes
        base_station_position = (5, 5)  # Fixed position for simplicity
        nodes_positions, node_energies = get_node_positions_and_energy(num_nodes)

        wban = WBAN(nodes_positions, base_station_position, node_energies)
        rounds = int(input("Enter the number of simulation rounds: "))  # Get number of rounds
        wban.simulate(rounds)
        wban.plot_energy_levels()
    except ValueError as e:
        print(f"Error: {e}. Please ensure you enter valid numbers.")
