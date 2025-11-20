from random_agents.agent import RandomAgent, ObstacleAgent, FloorAgent, StationAgent
from random_agents.model import RandomModel

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
    make_plot_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def random_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, RandomAgent):
        portrayal.color = "red"
    elif isinstance(agent, ObstacleAgent):
        portrayal.color = "gray"
        portrayal.marker = "s"
        portrayal.size = 100
    elif isinstance(agent, FloorAgent):
        portrayal.color = "brown"
        portrayal.marker = "^"
        portrayal.size = 10
    elif isinstance(agent, StationAgent):
        portrayal.color = "blue"
        portrayal.marker = "s"
        portrayal.size = 10
        # portrayal.edgecolors = "black"

    return portrayal

def post_process(ax):
    ax.set_aspect("equal")

def post_process_lines(ax):
    """Format the line plot"""
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))

model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "num_agents": Slider("Number of agents", 10, 1, 50),
    "width": Slider("Grid width", 20, 1, 50),
    "height": Slider("Grid height", 20, 1, 50),
    "num_obstacles": Slider("Number of obstacles", 15, 1, 50),
    "num_dirty_tiles": Slider("Number of dirty tiles", 20, 1, 50),
    "max_steps": Slider("Maximum number of steps", 100, 1, 500)
}

# Create the model using the initial parameters from the settings
model = RandomModel(
    num_agents=model_params["num_agents"].value,
    width=model_params["width"].value,
    height=model_params["height"].value,
    seed=model_params["seed"]["value"]
)

space_component = make_space_component(
        random_portrayal,
        draw_grid = False,
        post_process=post_process
)

# Graphic component for plotting clean percentage
lineplot_component = make_plot_component(
    {
        "clean_percentage": "orange",
        "num_agents": "blue",
        "average_energy": "green",
        "average_movements": "purple"
    },
    post_process=post_process_lines,
)

page = SolaraViz(
    model,
    components=[space_component, lineplot_component],
    model_params=model_params,
    name="Random Model",
)
