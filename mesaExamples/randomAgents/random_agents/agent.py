from mesa.discrete_space import CellAgent, FixedAgent

STATE_CHARGING = "CHARGING"
STATE_SEEKING_CHARGER = "SEEKING_CHARGER"
STATE_CLEANING = "CLEANING"
STATE_WANDERING = "WANDERING"
STATE_DEAD = "DEAD"

class RandomAgent(CellAgent):
    def __init__(self, model, cell, energy=100, energy_usage=1, energy_station=5, score=0):
        super().__init__(model)
        self.energy = energy
        self.energy_from_tile = energy_usage
        self.energy_station = energy_station
        self.score = score
        self.cell = cell
        self.known_stations = [cell]
        self.current_state = STATE_WANDERING
        self.movements = 0 

    def step(self):
        """
        Agent lifecycle per step
        """
        # 1. Perception (Sensors)
        self.discover_stations()
        
        # 2. Decision Making (Transitions)
        self.current_state = self.determine_next_state()
        
        # 3. Action Execution
        self.execute_state_action()
        
        # 4. Check for death condition
        if self.energy < 0:
            self.remove()

    def determine_next_state(self):
        """
        Decision making hierarchy - determines next state based on priorities
        """
        # Priority 1: If on a charging station and needs energy -> STATE_CHARGING
        is_on_station = any(isinstance(obj, StationAgent) for obj in self.cell.agents)
        if is_on_station and self.energy < 100:
            return STATE_CHARGING

        # Priority 2: If low battery -> STATE_SEEKING_CHARGER
        if self.energy < 50:
            return STATE_SEEKING_CHARGER

        # Priority 3: If on a dirty tile -> STATE_CLEANING
        is_on_dirty_tile = any(isinstance(obj, FloorAgent) and not obj.fully_clean for obj in self.cell.agents)
        if is_on_dirty_tile:
            return STATE_CLEANING

        # Priority 4: Default state -> Wander (explore)
        return STATE_WANDERING

    def execute_state_action(self):
        """
        Execute action based on current state (no decision making here)
        """
        if self.current_state == STATE_CHARGING:
            self.charge()
            
        elif self.current_state == STATE_SEEKING_CHARGER:
            self.move_to_station()
            
        elif self.current_state == STATE_CLEANING:
            self.clean()
            
        elif self.current_state == STATE_WANDERING:
            self.wander()

    # --- ACTIONS (State behaviors) ---

    def charge(self):
        """Charge battery at current station"""
        station = next((obj for obj in self.cell.agents if isinstance(obj, StationAgent)), None)
        if station:
            self.energy = min(100, self.energy + self.energy_station)

    def clean(self):
        """Clean the current dirty floor tile"""
        floor_tile = next((obj for obj in self.cell.agents if isinstance(obj, FloorAgent)), None)
        if floor_tile and not floor_tile.fully_clean:
            self.discharge()
            floor_tile.fully_clean = True
            self.score += 1
            self.movements += 1

    def move_to_station(self):
        """Move one step closer to the nearest known charging station"""
        nearest_station = self.find_nearest_station()
        
        # If no stations known or already at station (but not charging), wander instead
        if nearest_station is None or nearest_station == self.cell:
            self.wander() 
            return

        # Calculate movement towards station
        station_x, station_y = nearest_station.coordinate
        
        empty_neighbors = self.get_empty_neighbors()
        if not empty_neighbors:
            return 

        # Select neighbor cell closest to station (Manhattan distance)
        best_cell = min(
            empty_neighbors,
            key=lambda cell: abs(cell.coordinate[0] - station_x) + abs(cell.coordinate[1] - station_y)
        )
        self.move_agent(best_cell)

    def wander(self):
        """Explore randomly, preferring dirty tiles if visible"""
        empty_neighbors = self.get_empty_neighbors()
        if not empty_neighbors:
            return

        # Prioritize dirty tiles in neighboring cells
        cells_with_dirty_tiles = empty_neighbors.select(
            lambda cell: any(isinstance(obj, FloorAgent) and not obj.fully_clean for obj in cell.agents)
        )
        
        target_cells = cells_with_dirty_tiles if len(cells_with_dirty_tiles) > 0 else empty_neighbors
        random_cell = target_cells.select_random_cell()
        
        self.move_agent(random_cell)

    def move_agent(self, target_cell):
        """Helper to move agent and consume energy (avoids code duplication)"""
        self.cell = target_cell
        self.discharge()
        self.movements += 1

    # --- UTILITIES (Support functions) ---

    def get_empty_neighbors(self):
        """Get all neighboring cells that don't contain obstacles"""
        return self.cell.neighborhood.select(
            lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
        )

    def discharge(self):
        """Reduce energy from movement/cleaning"""
        self.energy -= self.energy_from_tile

    def discover_stations(self):
        """Discover charging stations in neighborhood and share with other agents"""
        for neighbor_cell in self.cell.neighborhood:
            if any(isinstance(obj, StationAgent) for obj in neighbor_cell.agents):
                self.share_station_location(neighbor_cell)
                # Share discovery with all other agents
                for agent in self.model.agents:
                    if isinstance(agent, RandomAgent) and agent != self:
                        agent.share_station_location(neighbor_cell)

    def share_station_location(self, station_cell):
        """Add a newly discovered station to known stations list"""
        if station_cell not in self.known_stations:
            self.known_stations.append(station_cell)

    def find_nearest_station(self):
        """Find the closest known charging station (Manhattan distance)"""
        if not self.known_stations:
            return None
        current_x, current_y = self.cell.coordinate
        return min(
            self.known_stations,
            key=lambda s: abs(s.coordinate[0] - current_x) + abs(s.coordinate[1] - current_y)
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
        # Remove agent when fully cleaned (causes percentage calculation issues)
        if self._fully_clean == True:
            self.remove()
