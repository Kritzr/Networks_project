import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import random

class SensorNode:
    def __init__(self, node_id, x, y, battery, is_sink=False):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.battery = battery
        self.is_sink = is_sink

    def consume_energy(self, amount):
        self.battery = max(0, self.battery - amount)

class WBANApp:
    def __init__(self, master):
        self.master = master
        self.master.title("WBAN Simulation Tool")
        
        # Variables and setup
        self.nodes = []
        self.network = nx.DiGraph()  # Directed graph
        self.energy_data = {'Dijkstra': [], 'ACO': [], 'GA': []}
        self.selected_node = None  # For selecting nodes to create edges
        
        # User Input Fields
        self.algorithm_label = tk.Label(master, text="Algorithm:")
        self.algorithm_label.grid(row=0, column=0)
        self.algorithm_choice = ttk.Combobox(master, values=["Dijkstra", "ACO", "GA"])
        self.algorithm_choice.grid(row=0, column=1)

        self.node_count_label = tk.Label(master, text="Number of Nodes:")
        self.node_count_label.grid(row=1, column=0)
        self.node_count_entry = tk.Entry(master)
        self.node_count_entry.grid(row=1, column=1)

        self.sink_count_label = tk.Label(master, text="Number of Sinks:")
        self.sink_count_label.grid(row=2, column=0)
        self.sink_count_entry = tk.Entry(master)
        self.sink_count_entry.grid(row=2, column=1)

        self.battery_label = tk.Label(master, text="Battery Life (0-100):")
        self.battery_label.grid(row=3, column=0)
        self.battery_entry = tk.Entry(master)
        self.battery_entry.grid(row=3, column=1)

        self.rounds_label = tk.Label(master, text="Number of Rounds:")
        self.rounds_label.grid(row=4, column=0)
        self.rounds_entry = tk.Entry(master)
        self.rounds_entry.grid(row=4, column=1)

        self.setup_button = tk.Button(master, text="Setup Nodes", command=self.setup_nodes)
        self.setup_button.grid(row=5, column=0, columnspan=2)

        self.start_sim_button = tk.Button(master, text="Start Simulation", command=self.run_simulation)
        self.start_sim_button.grid(row=6, column=0, columnspan=2)

        # Canvas for node placement
        self.canvas = tk.Canvas(master, width=500, height=400, bg="white")
        self.canvas.grid(row=7, column=0, columnspan=2)
        self.canvas.bind("<Button-1>", self.canvas_click)

        # Graph for comparison
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.comparison_canvas = FigureCanvasTkAgg(self.fig, master)
        self.comparison_canvas.get_tk_widget().grid(row=8, column=0, columnspan=2)
        
        # Storage for nodes and simulation settings
        self.node_positions = {}
        self.rounds = 0
        self.node_count_remaining = 0
        self.sink_count_remaining = 0

    def setup_nodes(self):
        # Fetch user input
        try:
            self.node_count_remaining = int(self.node_count_entry.get())
            self.sink_count_remaining = int(self.sink_count_entry.get())
            self.rounds = int(self.rounds_entry.get())
            initial_battery = int(self.battery_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values for setup.")
            return
        
        # Resetting everything
        self.nodes = []
        self.node_positions = {}
        self.network.clear()
        self.energy_data = {'Dijkstra': [], 'ACO': [], 'GA': []}
        self.canvas.delete("all")
        
        tk.messagebox.showinfo("Setup", "Place sinks first, then regular nodes.")
    
    def canvas_click(self, event):
        if self.node_count_remaining > 0 or self.sink_count_remaining > 0:
            self.add_node(event)
        else:
            self.add_edge(event)

    def add_node(self, event):
        if self.node_count_remaining <= 0 and self.sink_count_remaining <= 0:
            return

        is_sink = self.sink_count_remaining > 0
        color = "red" if is_sink else "blue"
        
        node_id = len(self.nodes)
        x, y = event.x, event.y
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill=color)
        
        battery = int(self.battery_entry.get())
        new_node = SensorNode(node_id, x, y, battery, is_sink)
        self.nodes.append(new_node)
        self.node_positions[node_id] = (x, y)
        self.network.add_node(node_id, pos=(x, y), battery=battery, is_sink=is_sink)

        if is_sink:
            self.sink_count_remaining -= 1
        else:
            self.node_count_remaining -= 1

    def add_edge(self, event):
        clicked_node = None
        min_distance = float('inf')
        for node in self.nodes:
            dist = np.sqrt((event.x - node.x) ** 2 + (event.y - node.y) ** 2)
            if dist < min_distance and dist < 15:
                min_distance = dist
                clicked_node = node

        if clicked_node is not None:
            if self.selected_node is None:
                self.selected_node = clicked_node
            else:
                start_node = self.selected_node
                end_node = clicked_node
                distance = np.sqrt((start_node.x - end_node.x) ** 2 + (start_node.y - end_node.y) ** 2)
                self.network.add_edge(start_node.node_id, end_node.node_id, weight=distance)
                self.canvas.create_line(start_node.x, start_node.y, end_node.x, end_node.y, arrow=tk.LAST)
                self.selected_node = None

    def run_simulation(self):
        selected_algorithm = self.algorithm_choice.get()
        if selected_algorithm == "Dijkstra":
            self.simulate_dijkstra()
        elif selected_algorithm == "ACO":
            self.simulate_aco()
        elif selected_algorithm == "GA":
            self.simulate_ga()
        
        self.plot_comparison()
        self.show_results_table()

    def calculate_energy_consumption(self, distance, energy_per_unit=0.5):
        return distance * energy_per_unit

    def simulate_dijkstra(self):
        sink_nodes = [node.node_id for node in self.nodes if node.is_sink]
        for node in self.nodes:
            node.battery = int(self.battery_entry.get())

        for _ in range(self.rounds):
            energy_consumed = 0
            for node in self.nodes:
                if node.is_sink or node.battery <= 10:
                    continue
                min_path_cost = float('inf')
                for sink in sink_nodes:
                    if nx.has_path(self.network, node.node_id, sink):
                        path = nx.shortest_path(self.network, node.node_id, sink, weight="weight")
                        path_cost = sum(self.network[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))
                        min_path_cost = min(min_path_cost, path_cost)

                if min_path_cost < float('inf'):
                    energy_decrement = self.calculate_energy_consumption(min_path_cost)
                    energy_consumed += energy_decrement
                    node.consume_energy(energy_decrement)

            self.energy_data['Dijkstra'].append(energy_consumed)

    def simulate_aco(self):
        for _ in range(self.rounds):
            energy_consumed = 0
            for node in self.nodes:
                if not node.is_sink and node.battery > 10:
                    distance = random.uniform(10, 50)
                    energy_decrement = self.calculate_energy_consumption(distance)
                    energy_consumed += energy_decrement
                    node.consume_energy(energy_decrement)
            self.energy_data['ACO'].append(energy_consumed)

    def simulate_ga(self):
        for _ in range(self.rounds):
            energy_consumed = 0
            for node in self.nodes:
                if not node.is_sink and node.battery > 10:
                    distance = random.uniform(15, 45)
                    energy_decrement = self.calculate_energy_consumption(distance)
                    energy_consumed += energy_decrement
                    node.consume_energy(energy_decrement)
            self.energy_data['GA'].append(energy_consumed)

    def plot_comparison(self):
        self.ax.clear()
        self.ax.plot(self.energy_data['Dijkstra'], label="Dijkstra", color='blue')
        self.ax.plot(self.energy_data['ACO'], label="ACO", color='green')
        self.ax.plot(self.energy_data['GA'], label="GA", color='red')
        self.ax.set_title("Energy Consumption Comparison")
        self.ax.set_xlabel("Rounds")
        self.ax.set_ylabel("Energy Consumed")
        self.ax.legend()
        self.comparison_canvas.draw()

    def show_results_table(self):
        print(f"Results after {self.rounds} rounds.")
        for node in self.nodes:
            print(f"Node {node.node_id} - Battery: {node.battery}")

# Run the application
root = tk.Tk()
app = WBANApp(root)
root.mainloop()
