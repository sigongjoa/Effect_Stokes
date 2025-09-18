import os
import subprocess
import json
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class SimulationAgent:
    def __init__(self):
        self.llm = LLMInterface()
        self.output_dir = "/workspace/outputs"
        os.makedirs(self.output_dir, exist_ok=True)

    def run_simulation(self, params: dict):
        print(f"[SimulationAgent] Running simulation with params: {params}")

        # 1. Generate Blender script using LLM
        blender_script_content = self.llm.generate_code(
            "blender_simulation_script",
            params
        )

        if not blender_script_content:
            raise ValueError("LLM failed to generate Blender simulation script.")

        # 2. Save the script to a temporary file
        script_path = os.path.join(self.output_dir, "temp_simulation_script.py")
        with open(script_path, "w") as f:
            f.write(blender_script_content)
        print(f"[SimulationAgent] Generated Blender script saved to: {script_path}")

        # Define output paths based on params
        vfx_type = params.get("vfx_type", "default_vfx").replace(" ", "_")
        blend_file_name = f"scene_setup_{vfx_type}.blend"
        blend_file_path = os.path.join(self.output_dir, blend_file_name)
        sim_cache_path = os.path.join(self.output_dir, "cache", f"{vfx_type}_sim")

        # Ensure the script uses these paths
        # (The prompt template should ideally guide the LLM to use these paths)
        # For now, we assume the LLM-generated script will use the paths specified in the prompt template.

        # 3. Execute Blender in headless mode with the script
        try:
            # Assuming blender executable is in the PATH or specified in Dockerfile
            # The Dockerfile for blender_runner service should have blender installed.
            command = [
                "blender",
                "--background",
                "--python", script_path,
                "--", # Separator for arguments to the python script
                blend_file_path, # Pass blend_file_path as an argument to the script
                sim_cache_path # Pass sim_cache_path as an argument to the script
            ]
            print(f"[SimulationAgent] Running Blender command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("[SimulationAgent] Blender Stdout:", result.stdout)
            if result.stderr:
                print("[SimulationAgent] Blender Stderr:", result.stderr)

        except FileNotFoundError:
            print("[SimulationAgent] Error: Blender executable not found. Make sure Blender is installed and in your PATH.")
            raise
        except subprocess.CalledProcessError as e:
            print(f"[SimulationAgent] Error during Blender execution: {e}")
            print("[SimulationAgent] Blender Stdout:", e.stdout)
            print("[SimulationAgent] Blender Stderr:", e.stderr)
            raise
        except Exception as e:
            print(f"[SimulationAgent] An unexpected error occurred: {e}")
            raise

        print(f"[SimulationAgent] Simulation completed. Blend file: {blend_file_path}, Cache: {sim_cache_path}")
        return {"sim_cache_path": sim_cache_path, "blend_file_path": blend_file_path}