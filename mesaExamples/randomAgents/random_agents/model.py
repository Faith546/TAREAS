import mesa
from mesa.discrete_space import OrthogonalMooreGrid
from mesa.datacollection import DataCollector
import time

from .agent import RandomAgent, ObstacleAgent, FloorAgent, StationAgent


class RandomModel(mesa.Model):
    """
    Creates a new model with random agents.
    Args:
        num_agents: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def __init__(self, num_agents=10, num_obstacles=15, num_dirty_tiles=20, width=8, height=8, seed=42, max_steps= 200, current_step= 0):

        super().__init__(seed=seed)
        self.num_agents = num_agents
        self.num_obstacles = num_obstacles
        self.num_dirty_tiles = num_dirty_tiles
        self.seed = seed
        self.width = width
        self.height = height
        self.max_steps = max_steps
        self.current_step = current_step
        self.initial_dirty_tiles = num_dirty_tiles

        

        self.grid = OrthogonalMooreGrid([width, height], torus=False)

        self.datacollector = DataCollector(
            model_reporters={
                "clean_percentage": lambda m: self._get_clean_percentage(m),
                "num_agents": lambda m: len([agent for agent in m.agents if isinstance(agent, RandomAgent)]),
                "average_energy": lambda m: self._get_average_energy(m),
                "average_movements": lambda m: self._get_average_movements(m)
            },
            agent_reporters={
                "Movements": "movements",
                "Score": "score",
                "Energy": "energy"
            }
        )

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


        if self.num_agents == 1:
            specific_cell = self.grid[(1,1)]
            StationAgent(self, cell= specific_cell)
            RandomAgent(self, cell= specific_cell)
        else:
            RandomAgent.create_agents(
                self,
                self.num_agents,
                cell=agent_cells,
            )

            for cell in agent_cells:
                StationAgent(self, cell=cell)



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
        
        # Retrieve initial data
        self.datacollector.collect(self)

    def step(self):
        '''Advance the model by one step.'''
        self.agents.shuffle_do("step")
        self.datacollector.collect(self) 

        # Verify if all cells are clean
        dirty_count = sum(1 for a in self.agents if isinstance(a, FloorAgent) and not a.fully_clean)
        if dirty_count == 0:
            self.running = False
            return

        # Verify maximum steps
        if self.current_step >= self.max_steps:
            self.running = False
            return

        # Verify active agents
        if len([agent for agent in self.agents if isinstance(agent, RandomAgent)]) == 0:
            self.running = False

        self.current_step += 1
    
    # Helpers
    
    def _get_clean_percentage(self, model):
        dirty_count = sum(1 for a in model.agents if isinstance(a, FloorAgent) and not a.fully_clean)
        return ((self.initial_dirty_tiles - dirty_count) / self.initial_dirty_tiles) * 100
    
    def _get_average_energy(self, model):
        agents = [agent for agent in model.agents if isinstance(agent, RandomAgent)]
        if not agents:
            return 0
        return sum(agent.energy for agent in agents) / len(agents)
    
    def _get_average_movements(self, model):
        """Calcula el promedio de movimientos de los RandomAgents"""
        agents = [agent for agent in model.agents if isinstance(agent, RandomAgent)]
        if not agents:
            return 0
        return sum(agent.movements for agent in agents) / len(agents)
