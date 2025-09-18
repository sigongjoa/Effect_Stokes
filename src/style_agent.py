import os
import subprocess
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class StyleAgent:
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

    def apply_style(self, sim_cache_path: str, params: dict, blend_file_path: str):
        print(f"[StyleAgent] Applying style to {blend_file_path} with params: {params}")

        # 1. Generate Blender script using LLM
        blender_script_content = self.llm.generate_code(
            "blender_style_script",
            {
                "style": params.get("style", "realistic"),
                "colors": params.get("colors", ["white"])
            }
        )

        if not blender_script_content:
            raise ValueError("LLM failed to generate Blender style script.")

        # 2. Save the script to a temporary file in the output directory
        script_filename = "temp_style_script.py"
        script_path_in_app = os.path.join(self.output_dir, script_filename)
        with open(script_path_in_app, "w") as f:
            f.write(blender_script_content)
        print(f"[StyleAgent] Generated Blender script saved to: {script_path_in_app}")

        # Define output path for the rendered image (path *inside* the blender_runner container)
        rendered_image_path_in_blender = os.path.join("/workspace/outputs", "styled_frame.png")

        # 3. Execute Blender in headless mode using docker run
        try:
            command = [
                "docker", "run", "--rm",
                "-w", "/tmp", # Set working directory to /tmp
                "-v", f"{self.output_dir}:/workspace/outputs", # Mount outputs directory
                "-v", f"{script_path_in_app}:/tmp/{script_filename}", # Mount the script
                
                "effect_stokes-blender_runner", # The image name of the blender_runner service
                "blender", blend_file_path, # Open the blend file (path inside blender_runner)
                "--background", "--python", f"/tmp/{script_filename}", "--",
                rendered_image_path_in_blender # Pass rendered_image_path as an argument to the script
            ]
            print(f"[StyleAgent] Running Docker command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("[StyleAgent] Docker Stdout:", result.stdout)
            if result.stderr:
                print("[StyleAgent] Docker Stderr:", result.stderr)

        except FileNotFoundError:
            print("[StyleAgent] Error: 'docker' command not found. Make sure Docker is installed and in your PATH.")
            raise
        except subprocess.CalledProcessError as e:
            print(f"[StyleAgent] Error during Docker/Blender execution: {e}")
            print("[StyleAgent] Docker Stdout:", e.stdout)
            print("[StyleAgent] Docker Stderr:", e.stderr)
            raise
        except Exception as e:
            print(f"[StyleAgent] An unexpected error occurred: {e}")
            raise

        print(f"[StyleAgent] Style applied and frame rendered: {rendered_image_path_in_blender}")
        return rendered_image_path_in_blender