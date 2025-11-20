
from mesa.discrete_space import CellAgent, FixedAgent

STATE_CHARGING = "CHARGING"
STATE_SEEKING_CHARGER = "SEEKING_CHARGER"
STATE_CLEANING = "CLEANING"
STATE_WANDERING = "WANDERING"
STATE_TRAVELING = "TRAVELING"
STATE_DEAD = "DEAD"

class RandomAgent(CellAgent):
  """
  Autonomous cleaning robot agent with state machine behavior.
  """
  def __init__(self, model, cell, energy=100, energy_usage=1, energy_station=5, score=0):
    """
    Create a new cleaning robot agent.
    
    Args:
      model: Model instance
      cell: Initial cell where agent is placed
      energy: Initial energy level
      energy_usage: Energy consumed per movement
      energy_station: Energy gained per step at charging station
      score: Initial cleaning score
    """
    super().__init__(model)
    self.energy = energy
    self.energy_from_tile = energy_usage
    self.energy_station = energy_station
    self.score = score
    self.movements = 0
    self.cell = cell
    self.previous_cell = None
    self.visited_cells = {}
    self.current_state = STATE_WANDERING
    self.known_stations = [cell]
    self.last_position_before_charging = None
    self.exploration_target = None
    self.visit_current_cell()

  def step(self):
    """Execute one step of agent behavior: sense, decide, act."""
    self.sense_environment()
    self.current_state = self.determine_next_state()
    self.execute_state_action()
    
    if self.energy < 0:
      self.remove()
  
  def determine_next_state(self):
    """Determine next state based on current situation and priorities."""
    is_on_station = any(isinstance(obj, StationAgent) for obj in self.cell.agents)
    if is_on_station and self.energy < 100:
      return STATE_CHARGING

    if self.energy < 25:
      if self.last_position_before_charging is None:
        self.last_position_before_charging = self.cell
      return STATE_SEEKING_CHARGER

    is_on_dirty_tile = any(isinstance(obj, FloorAgent) and not obj.fully_clean for obj in self.cell.agents)
    if is_on_dirty_tile:
      return STATE_CLEANING

    if self.exploration_target is not None:
      return STATE_TRAVELING

    return STATE_WANDERING

  def execute_state_action(self):
    """Execute action corresponding to current state."""
    if self.current_state == STATE_CHARGING:
      self.charge()
    elif self.current_state == STATE_SEEKING_CHARGER:
      self.move_to_station()
    elif self.current_state == STATE_CLEANING:
      self.clean()
    elif self.current_state == STATE_TRAVELING:
      self.move_to_exploration_target()
    elif self.current_state == STATE_WANDERING:
      self.wander()
  
  def sense_environment(self):
    """Gather information from environment."""
    self.discover_stations()
  
  def discover_stations(self):
    """Discover and share charging station locations with other agents."""
    for neighbor_cell in self.cell.neighborhood:
      if any(isinstance(obj, StationAgent) for obj in neighbor_cell.agents):
        self.share_station_location(neighbor_cell)
        for agent in self.model.agents:
          if isinstance(agent, RandomAgent) and agent != self:
            agent.share_station_location(neighbor_cell)
  
  def get_empty_neighbors(self):
    """Get neighboring cells without obstacles or other agents."""
    return self.cell.neighborhood.select(
      lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
      and not any(isinstance(obj, RandomAgent) for obj in cell.agents)
    )
  
  def is_station_occupied(self, station_cell):
    """Check if another agent is currently at the station."""
    agents_there = [
      obj for obj in station_cell.agents 
      if isinstance(obj, RandomAgent) and obj != self
    ]
    return len(agents_there) > 0

  def charge(self):
    """Charge battery at current station."""
    station = next((obj for obj in self.cell.agents if isinstance(obj, StationAgent)), None)
    if station:
      self.energy = min(100, self.energy + self.energy_station)

  def clean(self):
    """Clean the dirty floor tile at current position."""
    floor_tile = next((obj for obj in self.cell.agents if isinstance(obj, FloorAgent)), None)
    if floor_tile and not floor_tile.fully_clean:
      self.discharge()
      floor_tile.fully_clean = True
      self.score += 1
      self.movements += 1

  def move_to_station(self):
    """Move toward nearest available charging station."""
    target_station = self.find_best_station()    

    if target_station is None:
      self.wander()
      return

    if self.cell == target_station:
      return
    
    # Check if adjacent to target station
    dist_x = abs(self.cell.coordinate[0] - target_station.coordinate[0])
    dist_y = abs(self.cell.coordinate[1] - target_station.coordinate[1])
    distance = dist_x + dist_y

    if distance <= 1:
      if self.is_station_occupied(target_station):
        # Station occupied, wait without consuming energy
        return

    station_x, station_y = target_station.coordinate
    
    empty_neighbors = self.get_empty_neighbors()
    if not empty_neighbors:
      return 
    
    # Opportunistic cleaning on the way to station
    if self.energy > 15:
      dirty_neighbors = empty_neighbors.select(
        lambda cell: any(isinstance(obj, FloorAgent) and not obj.fully_clean for obj in cell.agents)
      )
      if len(dirty_neighbors) > 0:
        best_dirty = min(
          dirty_neighbors,
          key=lambda cell: abs(cell.coordinate[0] - station_x) + abs(cell.coordinate[1] - station_y)
        )
        self.move_agent(best_dirty)
        return

    # Filter previous cell to maintain inertia
    candidates = [c for c in empty_neighbors if c != self.previous_cell]
    if not candidates:
      candidates = empty_neighbors

    if not candidates:
      return

    best_cell = min(
      candidates,
      key=lambda cell: abs(cell.coordinate[0] - station_x) + abs(cell.coordinate[1] - station_y)
    )
    self.move_agent(best_cell)

  def wander(self):
    """Explore using least visited neighbor strategy with local minima detection."""
    if self.last_position_before_charging is not None:
      return self.return_to_saved_position()

    empty_neighbors = self.get_empty_neighbors()
    if not empty_neighbors:
      return

    cells_with_dirty_tiles = empty_neighbors.select(
      lambda cell: any(isinstance(obj, FloorAgent) and not obj.fully_clean for obj in cell.agents)
    )

    if len(cells_with_dirty_tiles) > 0:
      target_cell = cells_with_dirty_tiles.select_random_cell()
      self.move_agent(target_cell)
      return
    
    candidates_for_exploration = [
      cell for cell in empty_neighbors 
      if cell != self.previous_cell
    ]
    
    if len(candidates_for_exploration) == 0:
      candidates_for_exploration = empty_neighbors

    best_neighbor = min(
      candidates_for_exploration, 
      key=lambda cell: self.visited_cells.get(cell.coordinate, 0)
    )
    
    min_visits = self.visited_cells.get(best_neighbor.coordinate, 0)
    
    if min_visits >= 3:
      self.pick_exploration_target()
      return
    
    final_candidates = [
      cell for cell in candidates_for_exploration 
      if self.visited_cells.get(cell.coordinate, 0) == min_visits
    ]
    
    target = self.random.choice(final_candidates)
    self.move_agent(target)

  def return_to_saved_position(self):
    """Return to position saved before going to charge."""
    if self.last_position_before_charging is None:
      return
    
    if self.cell == self.last_position_before_charging:
      self.last_position_before_charging = None
      return
    
    target_x, target_y = self.last_position_before_charging.coordinate
    
    empty_neighbors = self.get_empty_neighbors()
    if not empty_neighbors:
      return
    
    best_cell = min(
      empty_neighbors,
      key=lambda cell: abs(cell.coordinate[0] - target_x) + abs(cell.coordinate[1] - target_y)
    )
    self.move_agent(best_cell)
  
  def move_to_exploration_target(self):
    """Move toward distant exploration target."""
    if self.exploration_target is None:
      return
    
    target_x, target_y = self.exploration_target
    
    if self.cell.coordinate == self.exploration_target:
      self.exploration_target = None
      return
    
    empty_neighbors = self.get_empty_neighbors()
    if not empty_neighbors:
      self.exploration_target = None
      return
    
    if self.energy > 15:
      dirty_neighbors = empty_neighbors.select(
        lambda cell: any(isinstance(obj, FloorAgent) and not obj.fully_clean for obj in cell.agents)
      )
      if len(dirty_neighbors) > 0:
        best_dirty = min(
          dirty_neighbors,
          key=lambda cell: abs(cell.coordinate[0] - target_x) + abs(cell.coordinate[1] - target_y)
        )
        self.move_agent(best_dirty)
        return
    
    best_cell = min(
      empty_neighbors,
      key=lambda cell: abs(cell.coordinate[0] - target_x) + abs(cell.coordinate[1] - target_y)
    )
    self.move_agent(best_cell)

  def move_agent(self, target_cell):
    """Move agent to target cell and update state."""
    self.previous_cell = self.cell
    self.cell = target_cell
    self.discharge()
    self.movements += 1
    self.visit_current_cell()

  def discharge(self):
    """Consume energy from movement or cleaning."""
    self.energy -= self.energy_from_tile

  def share_station_location(self, station_cell):
    """Add newly discovered station to known stations."""
    if station_cell not in self.known_stations:
      self.known_stations.append(station_cell)

  def find_best_station(self):
    """Find nearest available charging station."""
    if not self.known_stations:
      return None

    current_x, current_y = self.cell.coordinate
    
    def calculate_cost(station):
      dist = abs(station.coordinate[0] - current_x) + abs(station.coordinate[1] - current_y)
      if self.is_station_occupied(station):
        return dist + 10 
      return dist

    best_station = min(self.known_stations, key=calculate_cost)
    return best_station
  
  def visit_current_cell(self):
    """Register visit to current cell for exploration tracking."""
    pos = self.cell.coordinate
    if pos in self.visited_cells:
      self.visited_cells[pos] += 1
    else:
      self.visited_cells[pos] = 1
  
  def pick_exploration_target(self):
    """Select distant unvisited cell as exploration target."""
    for _ in range(10):
      rand_x = self.random.randrange(1, self.model.width - 1)
      rand_y = self.random.randrange(1, self.model.height - 1)
      pos = (rand_x, rand_y)
      
      if pos not in self.visited_cells:
        self.exploration_target = pos
        return
    
    self.exploration_target = (
      self.random.randrange(1, self.model.width - 1),
      self.random.randrange(1, self.model.height - 1)
    )


class ObstacleAgent(FixedAgent):
  """
  Obstacle agent. Blocks movement on the grid.
  """
  def __init__(self, model, cell):
    super().__init__(model)
    self.cell = cell

  def step(self):
    pass


class StationAgent(FixedAgent):
  """
  Charging station agent. Provides energy to RandomAgents when they step on it.
  """
  def __init__(self, model, cell):
    """
    Create a new charging station tile.
      
    Args:
      model: Model instance
      cell: Cell where this station is located
    """
    super().__init__(model)
    self.cell = cell

  def step(self):
    pass


class FloorAgent(FixedAgent):
  """
  Floor tile agent. Represents a cleanable surface that changes state when cleaned.
  """

  @property
  def fully_clean(self):
    """Whether the floor tile is fully clean."""
    return self._fully_clean

  @fully_clean.setter
  def fully_clean(self, value: bool) -> None:
    self._fully_clean = value

  def __init__(self, model, cell, is_clean=False):
    """
    Create a new floor tile.
    
    Args:
      model: Model instance
      cell: Cell where this floor tile is located
      is_clean: Whether the tile starts clean (False = dirty, True = clean)
    """
    super().__init__(model)
    self.cell = cell
    self._fully_clean = is_clean

  def step(self):
    if self._fully_clean == True:
      self.remove()
