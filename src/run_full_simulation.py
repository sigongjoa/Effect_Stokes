import sys
import os
import json

# Add the src directory to the Python path so we can import simulation_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from simulation_agent import SimulationAgent

if __name__ == "__main__":
    agent = SimulationAgent()

    # Default parameters
    default_simulation_params = {
        "grid_resolution": (101, 101),
        "time_steps": 30,
        "viscosity": 0.02,
        "initial_shape_position": (1.0, 1.0),
        "initial_shape_size": 0.4,
        "vortex_strength": 1.2,
    }
    default_visualization_params = {
        "arrow_color": (0.0, 0.0, 0.8),
        "arrow_scale_factor": 3.0,
        "arrow_density": 15,
    }
    effect_description = {
        "vfx_type": "swirling vortex",
        "style": "blue liquid"
    }

    # Parse parameters from command line if provided
    if len(sys.argv) > 1:
        try:
            # sys.argv[1] should be the JSON string for simulation_params
            provided_simulation_params = json.loads(sys.argv[1])
            # Merge provided params with defaults, provided takes precedence
            simulation_params_to_use = {**default_simulation_params, **provided_simulation_params}
        except json.JSONDecodeError:
            print("Error: Invalid JSON for simulation parameters provided.")
            sys.exit(1)
    else:
        simulation_params_to_use = default_simulation_params

    # Visualization params are not passed to run_full_simulation directly,
    # but inferred by SimulationAgent. We keep default_visualization_params
    # here for consistency with the original structure, though it's not used
    # as a direct override in agent.run_simulation() from this script.
    # The agent's internal inference logic will handle visualization_params.

    result = agent.run_simulation(
        effect_description=effect_description,
        simulation_params=simulation_params_to_use,
        # visualization_params are inferred by the agent, not directly passed from here
        # unless we want to override agent's inference. For now, let agent infer.
    )
    print(json.dumps(result, indent=2))

    # The "Next Steps for Blender Visualization" part is now handled by run_full_pipeline.py
    # so we can remove it from here.
