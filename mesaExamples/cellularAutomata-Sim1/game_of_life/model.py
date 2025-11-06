from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import Cell


class ConwaysGameOfLife(Model):
    """Represents the 2-dimensional array of cells in Conway's Game of Life."""

    def __init__(self, width=50, height=50, initial_fraction_alive=0.2, seed=None):
        """Create a new playing area of (width, height) cells."""
        super().__init__(seed=seed)

        """Grid where cells are connected to their 8 neighbors.

        Example for two dimensions:
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1),
        ]
        """

        # Se desactiva torus, ya que para este caso no se requiere la
        # conexión entre los lados del grid
        self.grid = OrthogonalMooreGrid((width, height), capacity=1, torus=False)

        # Place a cell at each location, with some initialized to
        # ALIVE and some to DEAD.
        for cell in self.grid.all_cells:
            Cell(
                self,
                cell,
                init_state=(
                    # Se inicializan células solo en la última fila del grid (49)
                    Cell.ALIVE
                    if self.random.random() < initial_fraction_alive and cell.coordinate[1] == 49
                    else Cell.DEAD
                ),
            )

        self.running = True

        # Se define el atributo current_row y se inicializa con el valor 48, que
        # es la siguiente fila después del estado inicial
        self.current_row = 48

    def step(self):
        """Perform the model step by updating one row at a time.s
        - First, all cells in the current row determine their next state
        - Then, all cells in the current row change state to their next state
        - Move to the next row down
        """
        # Cuando se llegue a la primera fila, la simulación termina, pues no hay
        # más filas para actualizar
        if self.current_row < 0:
            self.running = False
            return
        
        # Solo se actualizan las células de la fila actual a través de un ciclo
        # que las identifica en dicha fila
        cells_in_row = [agent for agent in self.agents if agent.y == self.current_row]
        
        # Para cada célula en la fila actual se usa la función para determinar
        # su estado
        for cell in cells_in_row:
            cell.determine_state()
        
        # Para cada célula en la fila actual se usa la función para cambiar su
        # estado
        for cell in cells_in_row:
            cell.assume_state()
        
        # Se mueve a la siguiente fila debajo
        self.current_row -= 1