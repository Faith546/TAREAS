# FixedAgent: Immobile agents permanently fixed to cells
from mesa.discrete_space import FixedAgent

class Cell(FixedAgent):
    """Represents a single ALIVE or DEAD cell in the simulation."""

    DEAD = 0
    ALIVE = 1

    @property
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    @property
    def neighbors(self):
        return self.cell.neighborhood.agents
    
    def __init__(self, model, cell, init_state=DEAD):
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model)
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    def determine_state(self):
        """Compute if the cell will be dead or alive at the next tick.  This is
        based on the number of alive or dead neighbors.  The state is not
        changed here, but is just computed and stored in self._nextState,
        because our current state may still be necessary for our neighbors
        to calculate their next state.
        """
        # Get the neighbors and apply the rules on whether to be alive or dead
        # at the next tick.

        # Se crean variables que corresponden a las posiciones de los vecinos de
        # arriba de la celda actual, por lo que unicamente se consideran 3
        # vecinos para la simulacion. Sa va a utilizar modulo para respetar el
        # toroide a traves de un wrapping. Ex:

        # Datos: 
        # Height=50 Width=50
        # self.pos = (5, 49)

        # left_pos = ((5 - 1) % 50, (49 + 1) % 50) = (4, 0)
        # center_pos = (5 % 50, 0) = (5, 0)
        # right_pos = ((5 + 1) % 50, 0) = (6, 0)

        width = self.model.grid.width
        height = self.model.grid.height

        left_pos = ((self.x-1) % width, (self.y+1) % height)
        center_pos = ((self.x) % width, (self.y+1) % height)
        right_pos = ((self.x+1) % width, (self.y+1) % height)

        # Inicializacion de variables donde se guardaran los agentes que
        # corresponen a los vecinos de arriba.
        left_agent = None
        center_agent = None
        right_agent = None

        # Ciclo donde se recorre la lista de 8 vecinos de la celula actual y se
        # identifican a los vecinos de arriba a traves de la igualdad de
        # posiciones (coordenadas) con las variables definidas previamente.
        for neighbor in self.neighbors:
            if neighbor.pos == left_pos:
                left_agent = neighbor
            elif neighbor.pos == center_pos:
                center_agent = neighbor
            elif neighbor.pos == right_pos:
                right_agent = neighbor

        # Para mayor legibilidad, se realizan nuevas variables que corresponden
        # a los 3 vecinos de arriba y evaluan que los agentes no sean None y que
        # esten vivos.
        left = 1 if (left_agent and left_agent.is_alive) else 0
        center = 1 if (center_agent and center_agent.is_alive) else 0
        right = 1 if (right_agent and right_agent.is_alive) else 0
        
        # Se aplican las siguientes reglas de estado de la celula con base en
        # los estados de los vecinos.
        if left == 1 and center == 1 and right == 1:
            self._next_state = self.DEAD  # 111 -> 0
        elif left == 1 and center == 1 and right == 0:
            self._next_state = self.ALIVE  # 110 -> 1
        elif left == 1 and center == 0 and right == 1:
            self._next_state = self.DEAD  # 101 -> 0
        elif left == 1 and center == 0 and right == 0:
            self._next_state = self.ALIVE  # 100 -> 1
        elif left == 0 and center == 1 and right == 1:
            self._next_state = self.ALIVE  # 011 -> 1
        elif left == 0 and center == 1 and right == 0:
            self._next_state = self.DEAD  # 010 -> 0
        elif left == 0 and center == 0 and right == 1:
            self._next_state = self.ALIVE  # 001 -> 1
        else:  # left == 0 and center == 0 and right == 0
            self._next_state = self.DEAD  # 000 -> 0


    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        self.state = self._next_state
