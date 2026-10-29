from simulation import Simulation
from visualization import Visualizer


simulation = Simulation(
    width=120,
    height=90,
    mutation_chance=0.005,
)

visualizer = Visualizer(simulation)
visualizer.run()
