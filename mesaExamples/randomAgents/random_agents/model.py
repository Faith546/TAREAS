import mesa
from mesa.discrete_space import OrthogonalMooreGrid
import time

from .agent import RandomAgent, ObstacleAgent, FloorAgent, StationAgent


class RandomModel(mesa.Model):
    """
    Creates a new model with random agents.
    Args:
        num_agents: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def __init__(self, num_agents=10, num_obstacles=15, num_dirty_tiles=20, width=8, height=8, seed=42, max_time_seconds=60):

        super().__init__(seed=seed)
        self.num_agents = num_agents
        self.num_obstacles = num_obstacles
        self.num_dirty_tiles = num_dirty_tiles
        self.seed = seed
        self.width = width
        self.height = height
        self.max_time_seconds = max_time_seconds
        self.start_time = time.time()
        

        self.grid = OrthogonalMooreGrid([width, height], torus=False)

        # self.datacollector = mesa.DataCollector(
        #     {
        #         "Dirty Tiles": lambda m: self.count_type(m, "Dirty Tiles"),
        #         "Clean Tiles": lambda m: self.count_type(m, "Clean Tiles"),
        #         "Roombas": lambda m: self.count_type(m, "Roombas"),
        #     }
        # )

        # Identify the coordinates of the border of the grid
        border = [(x,y)
                  for y in range(height)
                  for x in range(width)
                  if y in [0, height-1] or x in [0, width - 1]]

        # Create the border cells
        for _, cell in enumerate(self.grid):
            if cell.coordinate in border:
                ObstacleAgent(self, cell=cell)

        agent_cells = self.random.choices(self.grid.empties.cells, k=self.num_agents)

        RandomAgent.create_agents(
            self, # referencia del modelo
            self.num_agents,
            cell=agent_cells,
        )

        for cell in agent_cells:
            StationAgent(self, cell=cell)

        # specific_cell = self.grid[(1,1)]

        # StationAgent(self, cell= specific_cell)

        # RandomAgent(self, cell= specific_cell)

        FloorAgent.create_agents(
            self,
            self.num_dirty_tiles,
            cell=self.random.choices(self.grid.empties.cells, k=self.num_dirty_tiles)
        )

        ObstacleAgent.create_agents(
            self,
            self.num_obstacles,
            cell=self.random.choices(self.grid.empties.cells, k=self.num_obstacles)
        )

        self.running = True

    def step(self):
        '''Advance the model by one step.'''
        self.agents.shuffle_do("step")

        # if self.count_type(self, "Roombas") == 0:
        #     self.running = False

        elapsed_time = time.time() - self.start_time
        if elapsed_time >= self.max_time_seconds:
            self.running = False

        if len([agent for agent in self.agents if isinstance(agent, RandomAgent)]) == 0:
            self.running = False
