import os
import subprocess
import json
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class SimulationAgent:
    def __init__(self):
        self.llm = LLMInterface()
        # Determine output directory based on execution environment
        # If running inside Docker, it will be /app/workspace/outputs
        # If running on host for testing, it will be ./workspace/outputs
        if os.getenv("DOCKER_CONTAINER", "false") == "true":
            self.output_dir = "/app/workspace/outputs"
        else:
            self.output_dir = os.path.join(os.getcwd(), "workspace", "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    def run_simulation(self, params: dict):
        print(f"[SimulationAgent] Running simulation with params: {params}")

        # Define output paths for Blender (these are paths *inside* the blender_runner container)
        vfx_type = params.get("vfx_type", "default_vfx")
        # The LLM will handle the filename safety (replacing spaces with underscores)
        # within the generated Blender script.
        blend_file_name = f"scene_setup_{vfx_type.replace(' ', '_')}.blend" # This is for the Python agent's internal tracking
        blend_file_path_in_blender = os.path.join("/workspace/outputs", blend_file_name)
        sim_cache_path_in_blender = os.path.join("/workspace/outputs", "cache", f"{vfx_type.replace(' ', '_')}_sim")


        # 1. Generate Blender script using LLM
        blender_script_content = f"""
import bpy
import os
import sys

# Get arguments passed to the script
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
else:
    args = []

blend_file_path = args[0] if len(args) > 0 else "/workspace/outputs/scene_setup_default.blend"
sim_cache_path = args[1] if len(args) > 1 else "/workspace/outputs/cache/default_sim"

# Ensure output directory exists
output_dir = os.path.dirname(blend_file_path)
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.dirname(sim_cache_path), exist_ok=True) # Ensure cache dir exists

# --- Scene Setup ---
bpy.ops.wm.read_factory_settings(use_empty=True) # Start with a clean scene
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'

# Set animation frames based on duration
scene.frame_start = 1
scene.frame_end = int({params.get("duration", 3)} * 24) # Use passed duration

# --- Fluid Domain Setup ---
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
domain_obj = bpy.context.object
domain_obj.name = "FluidDomain"

bpy.ops.object.modifier_add(type='FLUID')
fluid_modifier = domain_obj.modifiers["Fluid"]
fluid_modifier.fluid_type = 'DOMAIN'
fluid_modifier.domain_settings.domain_type = 'GAS' # Assuming smoke/fire for now
fluid_modifier.domain_settings.resolution_max = 32
fluid_domain_settings = fluid_modifier.domain_settings
fluid_domain_settings.cache_directory = sim_cache_path # Use passed cache path
fluid_domain_settings.cache_type = 'ALL'
bpy.context.view_layer.update()


# --- Fluid Flow Object Setup (Example: Inflow) ---
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 0))
flow_obj = bpy.context.object
flow_obj.name = "FluidInflow"

bpy.ops.object.modifier_add(type='FLUID')
fluid_modifier = flow_obj.modifiers["Fluid"]
fluid_modifier.fluid_type = 'FLOW'
fluid_modifier.flow_settings.flow_type = 'SMOKE' # Assuming smoke/fire for now
fluid_modifier.flow_settings.flow_behavior = 'INFLOW' # Assuming smoke/fire for now
bpy.context.view_layer.update()

# --- Bake Simulation Data ---
bpy.context.view_layer.objects.active = domain_obj
domain_obj.select_set(True)
import time
time.sleep(0.1) # Add a small delay
# Iterate through all fluid domains and bake them
for ob in bpy.context.scene.objects:
    if ob.type == 'MESH' and ob.modifiers:
        for mod in ob.modifiers:
            if mod.type == 'FLUID' and mod.fluid_type == 'DOMAIN':
                # Ensure the domain object is active and selected for baking
                bpy.context.view_layer.objects.active = ob
                ob.select_set(True)
                # Bake the fluid data for this domain
                bpy.ops.fluid.bake_all()
                ob.select_set(False) # Deselect after baking


# --- Save .blend file ---
bpy.ops.wm.save_as_mainfile(filepath=blend_file_path) # Use passed blend file path
"""

        if not blender_script_content:
            raise ValueError("LLM failed to generate Blender simulation script.")

        print(f"[SimulationAgent] LLM Generated Blender Script Content:\n{blender_script_content}")

        # 2. Save the script to a temporary file in the output directory
        # This script will be mounted into the blender_runner container
        script_filename = "temp_simulation_script.py"
        script_path_in_app = os.path.join(self.output_dir, script_filename)
        with open(script_path_in_app, "w") as f:
            f.write(blender_script_content)
        print(f"[SimulationAgent] Generated Blender script saved to: {script_path_in_app}")

        # 3. Execute Blender in headless mode using docker run
        try:
            command = [
                "docker", "run", "--gpus", "all", "--rm",
                "-w", "/tmp", # Set working directory to /tmp
                "-v", f"{self.output_dir}:/workspace/outputs", # Mount outputs directory
                "-v", f"{script_path_in_app}:/tmp/{script_filename}", # Mount the script
                "effect_stokes-blender_runner", # The image name of the blender_runner service
                "blender", "--background", "--python", f"/tmp/{script_filename}", "--",
                blend_file_path_in_blender, # Pass blend_file_path as an argument to the script
                sim_cache_path_in_blender # Pass sim_cache_path as an argument to the script
            ]
            print(f"[SimulationAgent] Running Docker command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
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
            print(f"[SimulationAgent] An unexpected error occurred: {e}")
            raise

        print(f"[SimulationAgent] Simulation completed. Blend file: {blend_file_path_in_blender}, Cache: {sim_cache_path_in_blender}")

        # Convert container paths to host paths for return
        host_sim_cache_path = os.path.join(self.output_dir, os.path.relpath(sim_cache_path_in_blender, "/workspace/outputs"))
        host_blend_file_path = os.path.join(self.output_dir, os.path.relpath(blend_file_path_in_blender, "/workspace/outputs"))

        return {
            "sim_cache_path": host_sim_cache_path,
            "blend_file_path": host_blend_file_path
        }

    