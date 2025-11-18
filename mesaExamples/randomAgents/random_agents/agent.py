from mesa.discrete_space import CellAgent, FixedAgent

class RandomAgent(CellAgent):
    """
    Agent that moves randomly.
    Attributes:
        unique_id: Agent's ID
    """
    def __init__(self, model, cell, energy=100, energy_usage=1, energy_station=5, score=0):
        """
        Creates a new random agent.
        Args:
            model: Model reference for the agent
            cell: Reference to its position within the grid
            energy: Starting amount of energy
            energy_from_tile: Energy reduced from 1 unit of floor tile
        """
        super().__init__(model)
        self.energy = energy
        self.energy_from_tile = energy_usage
        self.energy_station = energy_station
        self.score = score
        self.cell = cell
        self.known_stations = [cell]
        
    def discharge(self):
        """If possible, discharge on the current floor tile"""
        self.energy -= self.energy_from_tile


    def clean(self):
        """If possible, clean the current floor tile"""
        floor_tile = next(
            obj for obj in self.cell.agents if isinstance(obj, FloorAgent)
        )
        if not floor_tile.fully_clean:
            self.discharge()
            floor_tile.fully_clean = True
            self.score += 1

    def charge(self):
        """If possible, charge on the current floor tile"""
        floor_tile = next(
            obj for obj in self.cell.agents if isinstance(obj, StationAgent)
        )
        if floor_tile:
            self.energy = min(100, self.energy + self.energy_station)

    def share_station_location(self, station_cell):
        """Add a new station to the list if it is unknown"""
        if station_cell not in self.known_stations:
            self.known_stations.append(station_cell)

    def find_nearest_station(self):
        """Find the known nearest station"""
        if not self.known_stations:
            return None

        current_x, current_y = self.cell.coordinate
        nearest_station = min(
            self.known_stations,
            key=lambda station: abs(station.coordinate[0] - current_x) + abs(station.coordinate[1] - current_y)
        )
        return nearest_station


    def move_to_station(self):
        """
        Moves one step closer to the charging station.
        """
        nearest_station = self.find_nearest_station()
        
        if nearest_station is None:
            return

        current_x, current_y = self.cell.coordinate
        station_x, station_y = nearest_station.coordinate

        if current_x == station_x and current_y == station_y:
            return

        empty_neighbors = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
        )

        if len(empty_neighbors) == 0:
            return
        
        best_cell = min(
            empty_neighbors,
            key=lambda cell: abs(cell.coordinate[0] - station_x) + abs(cell.coordinate[1] - station_y)
        )
        
        self.cell = best_cell
        self.discharge()

    def discover_stations(self):
        """Discover stations in the neighborhood and share them with other Agents"""
        for neighbor_cell in self.cell.neighborhood:
            if any(isinstance(obj, StationAgent) for obj in neighbor_cell.agents):
                self.share_station_location(neighbor_cell)

                for agent in self.model.agents:
                    if isinstance(agent, RandomAgent) and agent != self:
                        agent.share_station_location(neighbor_cell)


    def move(self):
        """
        Determines the new direction it will take, and then moves
        """
        empty_neighbors = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
        )

        if len(empty_neighbors) == 0:
            return
        
        cells_with_dirty_tiles = empty_neighbors.select(
            lambda cell: any(isinstance(obj, FloorAgent) and not obj.fully_clean for obj in cell.agents)
        )
        target_cells = (
            cells_with_dirty_tiles if len(cells_with_dirty_tiles) > 0 else empty_neighbors
        )
        self.cell = target_cells.select_random_cell()

        self.discharge()

    def step(self):
        """
        Determines the new direction it will take, and then moves
        """
        self.discover_stations()

        if any(isinstance(obj, StationAgent) for obj in self.cell.agents):
            if self.energy < 100:
                self.charge()
                return
            
        if self.energy < 50:
            self.move_to_station()
            return
        
        if any(isinstance(obj, FloorAgent) and not obj.fully_clean for obj in self.cell.agents):
            self.clean()

        self.move()

        if self.energy < 0:
            self.remove()


class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def step(self):
        pass

class StationAgent(FixedAgent):
    """
    Station agent. Energy supplier for a RandomAgent whenever it steps on it.
    """
    
    # @property
    # def fully_charged(self):
    #     """Whether the station is fully charged."""
    #     return self._fully_charged

    # @fully_charged.setter
    # def fully_charged(self, value: bool) -> None:
    #     """Set station recharging state and schedule recharging if not fully charged."""
    #     self._fully_charged = value

    #     if not value:
    #         self.model.simulator.schedule_event_relative(
    #             setattr,
    #             self.station_recharge_time,
    #             function_args=[self, "fully_charged", True],
    #         )

    def __init__(self, model, cell):

    # def __init__(self, model, cell, station_recharge_time, countdown):
        """
        Create a new station tile.
            
        Args:
            model: Model instance
            cell: Cell to which this station tile belongs
        """
        super().__init__(model)
        self.cell=cell
        # self._fully_charged = countdown == 0
        # self.station_recharge_time = station_recharge_time

        # if not self.fully_grown:
        #     self.model.simulator.schedule_event_relative(
        #         setattr, countdown, function_args=[self, "fully_charged", True]
        #     )


    def step(self):
            pass


class FloorAgent(FixedAgent):
    """
    Floor agent. Changes state whenever a RandomAgent steps on it.
    """

    @property
    def fully_clean(self):
        """Whether the floor is fully clean."""
        return self._fully_clean

    @fully_clean.setter
    def fully_clean(self, value: bool) -> None:
        self._fully_clean = value


    def __init__(self, model, cell, is_clean=False):
        """
        Create a new floor tile.
        
        Args:
            model: Model instance
            cell: Cell to which this floor tile belongs
            is_dirty: Whether the tile starts dirty (False = clean, True = dirty)
        """
        super().__init__(model)
        self.cell=cell
        self._fully_clean = is_clean

    def step(self):
        if self._fully_clean == True:
            self.remove()



