import os
import subprocess
import json
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class SimulationAgent:
    def __init__(self):
        self.llm = LLMInterface()
        if os.getenv("DOCKER_CONTAINER", "false") == "true":
            self.output_dir = "/app/workspace/outputs"
        else:
            self.output_dir = os.path.join(os.getcwd(), "workspace", "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    def run_simulation(self, effect_description: str, simulation_params: dict = None, visualization_params: dict = None):
        print(f"[SimulationAgent] Running simulation for: '{effect_description}'")

        # --- 1. LLM-like interpretation of effect_description and merging with explicit params ---
        # This is a simplified LLM interpretation. In a real scenario, an LLM would generate these.
        inferred_sim_params = {
            "grid_resolution": (81, 81),
            "time_steps": 1000,
            "viscosity": 0.05,
            "initial_shape_type": "crescent",
            "initial_shape_position": (0.5, 1.0),
            "initial_shape_size": 0.3,
            "initial_velocity": (0.5, 0.1),
            "boundary_conditions": "no_slip_walls",
            "vortex_strength": 0.0, # Default to no vortex
            "source_strength": 0.0, # Default to no source
        }
        inferred_viz_params = {
            "visualization_type": "arrows",
            "arrow_color": (0.0, 0.0, 1.0), # Default blue
            "arrow_scale_factor": 1.0,
            "arrow_density": 10,
        }

        # Simple keyword-based inference for demonstration
        if "vortex" in effect_description.lower() or "swirling" in effect_description.lower():
            inferred_sim_params["initial_shape_type"] = "vortex"
            inferred_sim_params["vortex_strength"] = 0.8
            inferred_sim_params["initial_velocity"] = (0.0, 0.0) # Vortex usually starts static
            inferred_sim_params["viscosity"] = 0.03 # Less viscous for clearer vortex
            inferred_sim_params["time_steps"] = 1500 # Longer to see vortex evolve
        if "red" in effect_description.lower():
            inferred_viz_params["arrow_color"] = (1.0, 0.0, 0.0)
        if "green" in effect_description.lower():
            inferred_viz_params["arrow_color"] = (0.0, 1.0, 0.0)
        if "fast" in effect_description.lower():
            inferred_sim_params["initial_velocity"] = (1.0, 0.2)
            inferred_sim_params["viscosity"] = 0.02
        if "slow" in effect_description.lower():
            inferred_sim_params["initial_velocity"] = (0.1, 0.05)
            inferred_sim_params["viscosity"] = 0.1
        if "explosion" in effect_description.lower() or "burst" in effect_description.lower():
            inferred_sim_params["initial_shape_type"] = "circle_burst"
            inferred_sim_params["initial_velocity"] = (0.0, 0.0) # Burst from center
            inferred_sim_params["source_strength"] = 0.5 # Add a source term
            inferred_sim_params["time_steps"] = 1200

        # Merge with explicit parameters, explicit params take precedence
        if simulation_params:
            inferred_sim_params.update(simulation_params)
        if visualization_params:
            inferred_viz_params.update(visualization_params)

        print(f"[SimulationAgent] Inferred Simulation Params: {inferred_sim_params}")
        print(f"[SimulationAgent] Inferred Visualization Params: {inferred_viz_params}")

        # Define paths
        fluid_data_dir = os.path.join(self.output_dir, "fluid_data")
        os.makedirs(fluid_data_dir, exist_ok=True)
        output_blend_file = os.path.join(self.output_dir, "fluid_simulation.blend")

        # --- 2. Run Python Navier-Stokes simulation to generate .npz data ---
        print("[SimulationAgent] Running Python Navier-Stokes simulation...")
        python_sim_script_path = os.path.join(os.getcwd(), "workspace", "navier_stokes_test.py")
        python_command = [
            os.path.join(os.getcwd(), "venv", "bin", "python"), # Path to venv python
            python_sim_script_path,
            json.dumps(inferred_sim_params) # Pass parameters as JSON string
        ]
        try:
            result = subprocess.run(python_command, capture_output=True, text=True, check=True)
            print("[SimulationAgent] Python Sim Stdout:", result.stdout)
            if result.stderr:
                print("[SimulationAgent] Python Sim Stderr:", result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"[SimulationAgent] Error during Python simulation: {e}")
            print("[SimulationAgent] Python Sim Stdout:", e.stdout)
            print("[SimulationAgent] Python Sim Stderr:", e.stderr)
            raise
        except Exception as e:
            print(f"[SimulationAgent] An unexpected error occurred during Python simulation: {e}")
            raise

        # --- 3. Run Blender script to visualize .npz data and save .blend file ---
        print("[SimulationAgent] Running Blender visualization script...")
        blender_viz_script_path = os.path.join(os.getcwd(), "workspace", "blender_fluid_visualizer.py")
        blender_command = [
            "docker", "run", "--gpus", "all", "--rm",
            "-v", f"{self.output_dir}:/workspace/outputs", # Mount outputs directory
            "-v", f"{blender_viz_script_path}:/tmp/blender_fluid_visualizer.py", # Mount the script
            "effect_stokes-blender_runner", # The image name of the blender_runner service
            "blender", "--background", "--python", "/tmp/blender_fluid_visualizer.py", "--",
            f"/workspace/outputs/fluid_data", # Pass fluid data directory (inside container)
            f"/workspace/outputs/fluid_simulation.blend", # Pass output blend file path (inside container)
            json.dumps(inferred_viz_params) # Pass visualization parameters as JSON string
        ]
        try:
            print(f"[SimulationAgent] Running Docker command: {' '.join(blender_command)}")
            result = subprocess.run(blender_command, capture_output=True, text=True, check=True)
            print("[SimulationAgent] Docker Stdout:", result.stdout)
            if result.stderr:
                print("[SimulationAgent] Docker Stderr:", result.stderr)
        except FileNotFoundError:
            print("[SimulationAgent] Error: 'docker' command not found. Make sure Docker is installed and in your PATH.")
            raise
        except subprocess.CalledProcessError as e:
            print(f"[SimulationAgent] Error during Docker/Blender execution: {e}")
            print("[SimulationAgent] Docker Stdout:", e.stdout)
            print("[SimulationAgent] Docker Stderr:", e.stderr)
            raise
        except Exception as e:
            print(f"[SimulationAgent] An unexpected error occurred during Blender visualization: {e}")
            raise

        print(f"[SimulationAgent] Simulation and visualization complete. Blender file: {output_blend_file}")

        return {
            "status": "success",
            "message": "Fluid effect generated successfully.",
            "output_file_path": output_blend_file,
            "inferred_simulation_params": inferred_sim_params,
            "inferred_visualization_params": inferred_viz_params
        }