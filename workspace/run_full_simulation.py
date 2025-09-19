
import sys
import os

# Add the src directory to the Python path so we can import simulation_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from simulation_agent import SimulationAgent

if __name__ == "__main__":
    agent = SimulationAgent()
    # You can pass parameters here if needed, e.g., duration, vfx_type
    # For now, we'll use default parameters as defined in the simulation_agent
    params = {"duration": 5, "vfx_type": "fluid_flow"}
    result = agent.run_simulation(params)
    print(f"Full simulation pipeline completed. Result: {result}")
