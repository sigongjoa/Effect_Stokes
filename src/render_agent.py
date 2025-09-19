import os
import subprocess
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class RenderAgent:
    def __init__(self):
        self.llm = LLMInterface()
        self.output_dir = "/workspace/outputs"
        os.makedirs(self.output_dir, exist_ok=True)

    def finalize_render(self, final_params: dict, blend_file_path: str):
        print(f"[RenderAgent] Finalizing render for {blend_file_path} with params: {final_params}")

        # 1. Generate Blender script using LLM
        blender_script_content = self.llm.generate_code(
            "blender_final_render_script",
            {
                "duration": final_params.get("duration", 3) # Default duration if not provided
            }
        )

        if not blender_script_content:
            raise ValueError("LLM failed to generate Blender final render script.")

        # 2. Save the script to a temporary file
        script_filename = "temp_final_render_script.py"
        script_path_in_app = os.path.join(self.output_dir, script_filename)
        with open(script_path_in_app, "w") as f:
            f.write(blender_script_content)
        print(f"[RenderAgent] Generated Blender script saved to: {script_path_in_app}")

        # Define output path for the final video (path *inside* the blender_runner container)
        final_video_path_in_blender = os.path.join("/workspace/outputs", "final_video.mp4")

        # 3. Execute Blender in headless mode using docker run
        try:
            command = [
                "docker", "run", "--rm",
                "-w", "/tmp", # Set working directory to /tmp
                "-v", f"{self.output_dir}:/workspace/outputs", # Mount outputs directory
                "-v", f"{script_path_in_app}:/tmp/{script_filename}", # Mount the script
                "-v", f"{blend_file_path}:{blend_file_path}", # Mount the blend file
                "effect_stokes-blender_runner", # The image name of the blender_runner service
                "blender", blend_file_path, # Open the blend file (path inside blender_runner)
                "--background", "--python", f"/tmp/{script_filename}", "--",
                final_video_path_in_blender # Pass final_video_path as an argument to the script
            ]
            print(f"[RenderAgent] Running Docker command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("[RenderAgent] Docker Stdout:", result.stdout)
            if result.stderr:
                print("[RenderAgent] Docker Stderr:", result.stderr)

        except FileNotFoundError:
            print("[RenderAgent] Error: 'docker' command not found. Make sure Docker is installed and in your PATH.")
            raise
        except subprocess.CalledProcessError as e:
            print(f"[RenderAgent] Error during Docker/Blender execution: {e}")
            print("[RenderAgent] Docker Stdout:", e.stdout)
            print("[RenderAgent] Docker Stderr:", e.stderr)
            raise
        except Exception as e:
            print(f"[RenderAgent] An unexpected error occurred: {e}")
            raise

        print(f"[RenderAgent] Final video rendered: {final_video_path_in_blender}")
        return final_video_path_in_blender