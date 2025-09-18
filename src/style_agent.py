import os
import subprocess
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class StyleAgent:
    def __init__(self):
        self.llm = LLMInterface()
        self.output_dir = "/workspace/outputs"
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

        # 2. Save the script to a temporary file
        script_path = os.path.join(self.output_dir, "temp_style_script.py")
        with open(script_path, "w") as f:
            f.write(blender_script_content)
        print(f"[StyleAgent] Generated Blender style script saved to: {script_path}")

        # Define output path for the rendered image
        rendered_image_path = os.path.join(self.output_dir, "styled_frame.png")

        # 3. Execute Blender in headless mode with the script
        try:
            command = [
                "blender",
                blend_file_path, # Open the blend file
                "--background",
                "--python", script_path,
                "--", # Separator for arguments to the python script
                rendered_image_path # Pass rendered_image_path as an argument to the script
            ]
            print(f"[StyleAgent] Running Blender command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("[StyleAgent] Blender Stdout:", result.stdout)
            if result.stderr:
                print("[StyleAgent] Blender Stderr:", result.stderr)

        except FileNotFoundError:
            print("[StyleAgent] Error: Blender executable not found. Make sure Blender is installed and in your PATH.")
            raise
        except subprocess.CalledProcessError as e:
            print(f"[StyleAgent] Error during Blender execution: {e}")
            print("[StyleAgent] Blender Stdout:", e.stdout)
            print("[StyleAgent] Blender Stderr:", e.stderr)
            raise
        except Exception as e:
            print(f"[StyleAgent] An unexpected error occurred: {e}")
            raise

        print(f"[StyleAgent] Style applied and frame rendered: {rendered_image_path}")
        return rendered_image_path