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
    infer_only = False
    if "--infer_only" in sys.argv:
        infer_only = True
        sys.argv.remove("--infer_only") # Remove it so argparse doesn't complain

    if infer_only:
        if len(sys.argv) > 1:
            try:
                effect_description_json = sys.argv[1]
                effect_description = json.loads(effect_description_json)
            except json.JSONDecodeError:
                print("Error: Invalid JSON for effect_description provided with --infer_only.", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: effect_description JSON not provided with --infer_only.", file=sys.stderr)
            sys.exit(1)

        inferred_sim_params, inferred_viz_params = agent.infer_parameters(effect_description)
        result = {
            "status": "success",
            "message": "Parameters inferred successfully.",
            "inferred_simulation_params": inferred_sim_params,
            "inferred_visualization_params": inferred_viz_params
        }
        # Ensure only the JSON output is printed to stdout
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # If not infer_only, proceed with full simulation
    simulation_params_to_use = default_simulation_params
    visualization_params_to_use = default_visualization_params

    if len(sys.argv) > 1:
        try:
            # sys.argv[1] should be the JSON string for simulation_params
            provided_simulation_params = json.loads(sys.argv[1])
            # Merge provided params with defaults, provided takes precedence
            simulation_params_to_use = {**default_simulation_params, **provided_simulation_params}
        except json.JSONDecodeError:
            print("Error: Invalid JSON for simulation parameters provided.", file=sys.stderr)
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            # sys.argv[2] should be the JSON string for visualization_params
            provided_visualization_params = json.loads(sys.argv[2])
            # Merge provided params with defaults, provided takes precedence
            visualization_params_to_use = {**default_visualization_params, **provided_visualization_params}
        except json.JSONDecodeError:
            print("Error: Invalid JSON for visualization parameters provided.", file=sys.stderr)
            sys.exit(1)

    result = agent.run_simulation(
        simulation_params=simulation_params_to_use,
        visualization_params=visualization_params_to_use
    )
    # Ensure only the JSON output is printed for the full simulation run as well
    print(json.dumps(result, indent=2))

    # The "Next Steps for Blender Visualization" part is now handled by run_full_pipeline.py
    # so we can remove it from here.
