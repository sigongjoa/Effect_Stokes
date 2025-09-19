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

    def run_simulation(self, params: dict):
        print(f"[SimulationAgent] Running simulation with params: {params}")

        # Define paths
        fluid_data_dir = os.path.join(self.output_dir, "fluid_data")
        os.makedirs(fluid_data_dir, exist_ok=True)
        output_blend_file = os.path.join(self.output_dir, "fluid_simulation.blend")

        # 1. Run Python Navier-Stokes simulation to generate .npz data
        print("[SimulationAgent] Running Python Navier-Stokes simulation...")
        python_sim_script_path = os.path.join(os.getcwd(), "workspace", "navier_stokes_test.py")
        python_command = [
            os.path.join(os.getcwd(), "venv", "bin", "python"), # Path to venv python
            python_sim_script_path
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

        # 2. Run Blender script to visualize .npz data and save .blend file
        print("[SimulationAgent] Running Blender visualization script...")
        blender_viz_script_path = os.path.join(os.getcwd(), "workspace", "blender_fluid_visualizer.py")
        blender_command = [
            "docker", "run", "--gpus", "all", "--rm",
            "-v", f"{self.output_dir}:/workspace/outputs", # Mount outputs directory
            "-v", f"{blender_viz_script_path}:/tmp/blender_fluid_visualizer.py", # Mount the script
            "effect_stokes-blender_runner", # The image name of the blender_runner service
            "blender", "--background", "--python", "/tmp/blender_fluid_visualizer.py", "--",
            f"/workspace/outputs/fluid_data", # Pass fluid data directory (inside container)
            f"/workspace/outputs/fluid_simulation.blend" # Pass output blend file path (inside container)
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
            "blend_file_path": output_blend_file
        }