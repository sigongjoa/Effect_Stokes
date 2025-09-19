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

    # --- Instructions for the user to visualize in Blender ---
    if result["status"] == "success":
        fluid_data_path = result["output_data_path"]
        print("\n--- Next Steps for Blender Visualization ---")
        print(f"Fluid simulation data has been generated and saved to: {fluid_data_path}")
        print("You can now use the 'workspace/blender_fluid_visualizer.py' script to visualize this data in Blender.")
        print("To do so, open Blender and run the script, passing the data path and desired output blend file:")
        print(f"blender --background --python /mnt/d/progress/Effect_Stokes/workspace/blender_fluid_visualizer.py -- {fluid_data_path} /mnt/d/progress/Effect_Stokes/workspace/outputs/my_custom_fluid_vfx.blend {json.dumps(result["inferred_visualization_params"])}")
        print("Remember to adjust the output blend file path as needed.")
