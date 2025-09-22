import sys
import os
import json

# Add the src directory to the Python path so we can import simulation_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from simulation_agent import SimulationAgent

if __name__ == "__main__":
    agent = SimulationAgent()

    # Default parameters are now handled by SimulationAgent's _validate_params
    # We only need to define effect_description for infer_only mode
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
            "simulation_params": inferred_sim_params, # Changed key name to match api_spec
            "visualization_params": inferred_viz_params # Changed key name to match api_spec
        }
        # Ensure only the JSON output is printed to stdout
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # If not infer_only, proceed with full simulation
    # Pass raw JSON strings to SimulationAgent, which will handle validation and defaults
    simulation_params_json = None
    visualization_params_json = None

    if len(sys.argv) > 1:
        simulation_params_json = sys.argv[1]
    if len(sys.argv) > 2:
        visualization_params_json = sys.argv[2]

    # Parse JSON strings here before passing to agent.run_simulation
    # The agent expects dicts, not JSON strings
    simulation_params_dict = json.loads(simulation_params_json) if simulation_params_json else {}
    visualization_params_dict = json.loads(visualization_params_json) if visualization_params_json else {}

    result = agent.run_simulation(
        simulation_params=simulation_params_dict,
        visualization_params=visualization_params_dict
    )
    # Ensure only the JSON output is printed for the full simulation run as well
    print(json.dumps(result, indent=2))

    # The "Next Steps for Blender Visualization" part is now handled by run_full_pipeline.py
    # so we can remove it from here.
