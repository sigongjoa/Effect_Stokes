
import os
import json
from src.llm_interface import LLMInterface
from src.prompt_templates import PROMPT_TEMPLATES
import numpy as np
from src.fluid_simulator import FluidSimulator # Import the new FluidSimulator
from src.param_evaluator import ParamEvaluator # Import ParamEvaluator

# Utility functions for parameter validation (adapted for function strings)
param_evaluator = ParamEvaluator() # Initialize ParamEvaluator

def _validate_type(value, expected_type, param_name):
    if expected_type == float and isinstance(value, int):
        return True, None # Allow int to be treated as float
    if not isinstance(value, expected_type):
        # If expected type is float/int, but value is string, try to evaluate it as a function
        if (expected_type == float or expected_type == int) and isinstance(value, str):
            try:
                # Temporarily evaluate at t=0 to check if it's a valid expression
                param_evaluator.evaluate(value, t=0)
                return True, None
            except ValueError:
                return False, f"Parameter '{param_name}' is a string but not a valid mathematical expression."
        return False, f"Parameter '{param_name}' must be of type {expected_type.__name__}"
    return True, None

def _validate_range(value, min_val, max_val, param_name):
    # If value is a string (function), we can't validate its range directly here.
    # The range validation will happen during evaluation at each timestep in FluidSimulator.
    if isinstance(value, str):
        return True, None
    if not (min_val <= value <= max_val):
        return False, f"Parameter '{param_name}' must be between {min_val} and {max_val}"
    return True, None

def _validate_list_length(value, expected_len, param_name):
    if not isinstance(value, list) or len(value) != expected_len:
        return False, f"Parameter '{param_name}' must be a list of length {expected_len}"
    return True, None

class SimulationAgent:
    def __init__(self):
        self.llm = LLMInterface()
        self.fluid_simulator = FluidSimulator() # Instantiate FluidSimulator
        if os.getenv("DOCKER_CONTAINER", "false") == "true":
            self.output_dir = "/app/workspace/outputs"
        else:
            self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    def _validate_params(self, sim_params: dict, viz_params: dict):
        # Define default values and validation rules for simulation parameters
        sim_validation_rules = {
            "grid_resolution": {"type": list, "len": 2, "item_type": int, "min_item": 20, "max_item": 200, "default": [101, 101]},
            "time_steps": {"type": int, "min": 10, "max": 2000, "default": 30},
            "viscosity": {"type": float, "min": 0.001, "max": 0.1, "default": 0.02},
            "initial_shape_type": {"type": str, "allowed": ["vortex", "crescent", "circle_burst"], "default": "vortex"},
            "initial_shape_position": {"type": list, "len": 2, "item_type": float, "min_item": 0.0, "max_item": 2.0, "default": [1.0, 1.0]},
            "initial_shape_size": {"type": float, "min": 0.1, "max": 1.0, "default": 0.4},
            "initial_velocity": {"type": list, "len": 2, "item_type": float, "min_item": -5.0, "max_item": 5.0, "default": [0.0, 0.0]},
            "boundary_conditions": {"type": str, "allowed": ["no_slip_walls"], "default": "no_slip_walls"},
            "vortex_strength": {"type": float, "min": 0.0, "max": 5.0, "default": 1.2},
            "source_strength": {"type": float, "min": 0.0, "max": 5.0, "default": 2.0},
        }

        # Define default values and validation rules for visualization parameters
        viz_validation_rules = {
            "arrow_color": {"type": list, "len": 3, "item_type": float, "min_item": 0.0, "max_item": 1.0, "default": [0.0, 0.0, 0.8]},
            "arrow_scale_factor": {"type": float, "min": 0.1, "max": 10.0, "default": 3.0},
            "arrow_density": {"type": int, "min": 1, "max": 50, "default": 15},
            "emission_strength": {"type": float, "min": 0.0, "max": 100.0, "default": 50.0},
            "transparency_alpha": {"type": float, "min": 0.0, "max": 1.0, "default": 0.1},
            "camera_location": {"type": list, "len": 3, "item_type": float, "min_item": -10.0, "max_item": 10.0, "default": [0, -5, 2]},
            "light_energy": {"type": float, "min": 0.0, "max": 10.0, "default": 3.0},
            "render_samples": {"type": int, "min": 1, "max": 4096, "default": 128},
        }

        # Validate and apply defaults for simulation parameters
        for param, rules in sim_validation_rules.items():
            value = sim_params.get(param)
            if value is None:
                sim_params[param] = rules["default"]
                continue

            is_valid, _ = _validate_type(value, rules["type"], param)
            if not is_valid:
                # If validation fails, use default. For function strings, this means the string was invalid.
                sim_params[param] = rules["default"]
                continue

            if rules["type"] == list:
                is_valid, _ = _validate_list_length(value, rules["len"], param)
                if not is_valid:
                    sim_params[param] = rules["default"]
                    continue
                for i, item in enumerate(value):
                    # For list items, if they are strings, they are not expected to be functions here
                    is_valid, _ = _validate_type(item, rules["item_type"], f"{param} item")
                    if not is_valid:
                        value[i] = rules["default"][i] if isinstance(rules["default"], list) and len(rules["default"]) > i else rules["item_type"]()
                        continue
                    is_valid, _ = _validate_range(item, rules["min_item"], rules["max_item"], f"{param} item")
                    if not is_valid:
                        value[i] = np.clip(item, rules["min_item"], rules["max_item"])
            elif rules["type"] in [int, float]:
                # If it's a string, _validate_type already checked if it's a valid expression
                # Range check for string expressions is skipped here, done at evaluation time in FluidSimulator.
                if not isinstance(value, str):
                    is_valid, _ = _validate_range(value, rules["min"], rules["max"], param)
                    if not is_valid:
                        sim_params[param] = np.clip(value, rules["min"], rules["max"])
            elif rules["type"] == str:
                if "allowed" in rules and value not in rules["allowed"]:
                    sim_params[param] = rules["default"]

        # Validate and apply defaults for visualization parameters
        for param, rules in viz_validation_rules.items():
            value = viz_params.get(param)
            if value is None:
                viz_params[param] = rules["default"]
                continue

            is_valid, _ = _validate_type(value, rules["type"], param)
            if not is_valid:
                viz_params[param] = rules["default"]
                continue

            if rules["type"] == list:
                is_valid, _ = _validate_list_length(value, rules["len"], param)
                if not is_valid:
                    viz_params[param] = rules["default"]
                    continue
                for i, item in enumerate(value):
                    is_valid, _ = _validate_type(item, rules["item_type"], f"{param} item")
                    if not is_valid:
                        value[i] = rules["default"][i] if isinstance(rules["default"], list) and len(rules["default"]) > i else rules["item_type"]()
                        continue
                    is_valid, _ = _validate_range(item, rules["min_item"], rules["max_item"], f"{param} item")
                    if not is_valid:
                        value[i] = np.clip(item, rules["min_item"], rules["max_item"])
            elif rules["type"] in [int, float]:
                if not isinstance(value, str):
                    is_valid, _ = _validate_range(value, rules["min"], rules["max"], param)
                    if not is_valid:
                        viz_params[param] = np.clip(value, rules["min"], rules["max"])
            elif rules["type"] == str:
                if "allowed" in rules and value not in rules["allowed"]:
                    viz_params[param] = rules["default"]

        return sim_params, viz_params

    def infer_parameters(self, effect_description: str):
        effect_keywords = effect_description
        
        # Use LLM to infer simulation and visualization parameters
        llm_response = self.llm.infer_simulation_and_visualization_parameters(effect_keywords)
        
        inferred_sim_params = llm_response.get("simulation_params", {})
        inferred_viz_params = llm_response.get("visualization_params", {})

        return inferred_sim_params, inferred_viz_params

    def run_simulation(self, simulation_params: dict, visualization_params: dict):
        # Validate and potentially correct parameters (either inferred or provided by user)
        final_sim_params, final_viz_params = self._validate_params(simulation_params, visualization_params)

        # Define paths
        fluid_data_dir = os.path.join(self.output_dir, "fluid_data")
        os.makedirs(fluid_data_dir, exist_ok=True)

        # --- 2. Run FluidSimulator to generate .npz data ---
        simulation_result = self.fluid_simulator.run_simulation(
            simulation_params=final_sim_params,
            output_dir=fluid_data_dir
        )

        return {
            "status": "success",
            "message": "Fluid data generated successfully.",
            "output_data_path": fluid_data_dir,
            "simulation_params": final_sim_params, # Original (potentially function-based) params
            "visualization_params": final_viz_params # Original (potentially function-based) viz params
        }
