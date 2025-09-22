
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
            self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    def run_simulation(self, effect_description: dict, simulation_params: dict = None, visualization_params: dict = None):

        # Extract a string for keyword-based inference
        effect_keywords = effect_description.get('vfx_type', '') + " " + effect_description.get('style', '')
        effect_keywords = effect_keywords.strip().lower()
        inferred_sim_params = {
            "grid_resolution": (81, 81),
            "time_steps": 1000,
            "viscosity": 0.01,
            "initial_shape_type": "slash",  # 기존 crescent → slash/arc 느낌
            "initial_shape_position": (0.5, 0.5),
            "initial_shape_size": 0.3,
            "initial_velocity": (0.0, 3.0),  # +Y 방향으로 강한 전진 속도
            "boundary_conditions": "no_slip_walls",
            "vortex_strength": 0.0,
            "source_strength": 2.0  # 지속적으로 유체 방출
        }
        inferred_viz_params = {
            "visualization_type": "arrows",
            "arrow_color": (0.0, 0.0, 1.0), # Default blue
            "arrow_scale_factor": 1.0,
            "arrow_density": 10,
        }

        # Simple keyword-based inference for demonstration
        if "vortex" in effect_keywords or "swirling" in effect_keywords:
            inferred_sim_params["initial_shape_type"] = "vortex"
            inferred_sim_params["vortex_strength"] = 0.8
            inferred_sim_params["initial_velocity"] = (0.0, 0.0) # Vortex usually starts static
            inferred_sim_params["viscosity"] = 0.03 # Less viscous for clearer vortex
            inferred_sim_params["time_steps"] = 1500 # Longer to see vortex evolve
        if "red" in effect_keywords:
            inferred_viz_params["arrow_color"] = (1.0, 0.0, 0.0)
        if "green" in effect_keywords:
            inferred_viz_params["arrow_color"] = (0.0, 1.0, 0.0)
        if "fast" in effect_keywords:
            inferred_sim_params["initial_velocity"] = (1.0, 0.2)
            inferred_sim_params["viscosity"] = 0.02
        if "slow" in effect_keywords:
            inferred_sim_params["initial_velocity"] = (0.1, 0.05)
            inferred_sim_params["viscosity"] = 0.1
        if "explosion" in effect_keywords or "burst" in effect_keywords:
            inferred_sim_params["initial_shape_type"] = "circle_burst"
            inferred_sim_params["initial_velocity"] = (0.0, 0.0) # Burst from center
            inferred_sim_params["source_strength"] = 0.5 # Add a source term
            inferred_sim_params["time_steps"] = 1200

        # Merge with explicit parameters, explicit params take precedence
        if simulation_params:
            inferred_sim_params.update(simulation_params)
        if visualization_params:
            inferred_viz_params.update(visualization_params)

        # Define paths
        fluid_data_dir = os.path.join(self.output_dir, "fluid_data")
        os.makedirs(fluid_data_dir, exist_ok=True)

        # --- 2. Run Python Navier-Stokes simulation to generate .npz data ---
        python_sim_script_path = os.path.join(os.getcwd(), "tests", "navier_stokes_test.py")
        python_command = [
            os.path.join(os.getcwd(), "venv", "bin", "python"), # Path to venv python
            python_sim_script_path,
            fluid_data_dir, # Pass the correct output directory
            json.dumps(inferred_sim_params) # Pass parameters as JSON string
        ]
        try:
            result = subprocess.run(python_command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise
        except Exception as e:
            raise

        return {
            "status": "success",
            "message": "Fluid data generated successfully.",
            "output_data_path": fluid_data_dir,
            "inferred_simulation_params": inferred_sim_params,
            "inferred_visualization_params": inferred_viz_params # Still return for info
        }
