import sys
import os
import json

# Add the src directory to the Python path so we can import simulation_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from simulation_agent import SimulationAgent

if __name__ == "__main__":
    agent = SimulationAgent()

    # --- Demonstrate Generalization with a new effect: "a swirling vortex of blue liquid" ---
    effect_description = "a swirling vortex of blue liquid"
    # Explicit parameters can override inferred ones or provide details not easily inferred
    simulation_params = {
        "grid_resolution": (101, 101), # Higher resolution
        "time_steps": 2000, # Longer simulation
        "viscosity": 0.02, # Clearer vortex
        "initial_shape_position": (1.0, 1.0), # Center the vortex
        "initial_shape_size": 0.4, # Larger vortex
        "vortex_strength": 1.2, # Stronger vortex
    }
    visualization_params = {
        "arrow_color": (0.0, 0.0, 0.8), # Darker blue
        "arrow_scale_factor": 3.0, # More pronounced arrows
        "arrow_density": 15, # Denser arrows
    }

    print(f"[run_full_simulation] Calling SimulationAgent with effect: '{effect_description}'")
    result = agent.run_simulation(
        effect_description=effect_description,
        simulation_params=simulation_params,
        visualization_params=visualization_params
    )
    print(f"[run_full_simulation] Full simulation pipeline completed. Result: {json.dumps(result, indent=2)}")