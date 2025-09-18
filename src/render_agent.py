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
        script_path = os.path.join(self.output_dir, "temp_final_render_script.py")
        with open(script_path, "w") as f:
            f.write(blender_script_content)
        print(f"[RenderAgent] Generated Blender script saved to: {script_path}")

        # Define output path for the final video
        final_video_path = os.path.join(self.output_dir, "final_video.mp4")

        # 3. Execute Blender in headless mode with the script
        try:
            command = [
                "blender",
                blend_file_path, # Open the blend file
                "--background",
                "--python", script_path,
                "--", # Separator for arguments to the python script
                final_video_path # Pass final_video_path as an argument to the script
            ]
            print(f"[RenderAgent] Running Blender command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("[RenderAgent] Blender Stdout:", result.stdout)
            if result.stderr:
                print("[RenderAgent] Blender Stderr:", result.stderr)

        except FileNotFoundError:
            print("[RenderAgent] Error: Blender executable not found. Make sure Blender is installed and in your PATH.")
            raise
        except subprocess.CalledProcessError as e:
            print(f"[RenderAgent] Error during Blender execution: {e}")
            print("[RenderAgent] Blender Stdout:", e.stdout)
            print("[RenderAgent] Blender Stderr:", e.stderr)
            raise
        except Exception as e:
            print(f"[RenderAgent] An unexpected error occurred: {e}")
            raise

        print(f"[RenderAgent] Final video rendered: {final_video_path}")
        return final_video_path