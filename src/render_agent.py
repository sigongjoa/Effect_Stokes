import json
import os
import subprocess
import sys
import shutil
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class RenderAgent:
    def __init__(self, llm_type: str = "ollama", llm_model: str = "llama2", llm_base_url: str = "http://localhost:11434"):
        self.llm = LLMInterface(llm_type=llm_type, model_name=llm_model, base_url=llm_base_url)
        if os.getenv("DOCKER_CONTAINER", "false") == "true":
            self.output_dir = "/app/workspace/outputs"
            self.project_root_in_docker = "/app"
        else:
            self.output_dir = os.path.join(os.getcwd(), "workspace", "outputs")
            self.project_root_in_docker = os.getcwd() # Assuming local execution, project root is current dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _render_frames_to_images(self, blend_file_path: str, output_image_dir: str):
        print(f"[RenderAgent] Rendering frames from {blend_file_path} to {output_image_dir}")
        os.makedirs(output_image_dir, exist_ok=True)

        # Blender command to render frames
        # Need to ensure paths are correct for Docker environment
        blend_file_path_in_docker = os.path.join("/app", os.path.relpath(blend_file_path, os.getcwd()))
        output_image_dir_in_docker = os.path.join("/app", os.path.relpath(output_image_dir, os.getcwd()))

        blender_render_command_args = [
            "blender",
            "--background",
            "--render-output", os.path.join(output_image_dir_in_docker, "frame_####"),
            "--render-format", "PNG",
            "-a", # Changed from --animation
            blend_file_path_in_docker # The blend file to open, as the last argument
        ]

        # Construct the Docker command
        docker_command = [
            "docker", "run", "--rm", "--gpus", "all",
            "-v", f"{os.getcwd()}:/app", # Mount project root
            "-w", "/app", # Set working directory inside container to /app
            "effect_stokes-blender_cuda_runner", # The image name of the blender_runner service
        ] + blender_render_command_args

        print(f"[RenderAgent] Running Docker render command: {' '.join(docker_command)}")
        try:
            # Stream output directly to console
            # Note: For real-time streaming, it's often better to use subprocess.Popen
            # and read line by line, but for simplicity and to avoid buffering issues
            # with subprocess.run, we'll let stdout/stderr inherit parent's streams.
            # We remove text=True because we're not capturing output as a string.
            process = subprocess.run(docker_command, check=True, stdout=sys.stdout, stderr=sys.stderr)
        except FileNotFoundError:
            print("[RenderAgent] Error: 'docker' command not found. Make sure Docker is installed and in your PATH.")
            raise
        except subprocess.CalledProcessError as e:
            print(f"[RenderAgent] Error during Blender frame rendering: {e}")
            # No need to print stdout/stderr here as it was streamed
            raise
        except Exception as e:
            print(f"[RenderAgent] An unexpected error occurred during Blender frame rendering: {e}")
            raise
        print(f"[RenderAgent] Frames rendered to {output_image_dir}")

    def render_vfx(self, fluid_data_path: str, output_blend_file: str, viz_params: dict) -> dict:
        print(f"[RenderAgent] Rendering VFX for fluid data: {fluid_data_path} to {output_blend_file}")

        # Convert viz_params to JSON string for passing to Blender script
        viz_params_json = json.dumps(viz_params)

        # Path to blender_fluid_visualizer.py relative to project root
        blender_script_path_relative = os.path.join("workspace", "blender_fluid_visualizer.py")
        blender_script_path_absolute = os.path.join("/app", blender_script_path_relative)

        # Define paths for Docker mounts and execution
        # fluid_data_path and output_blend_file need to be converted to Docker-internal paths
        fluid_data_path_in_docker = os.path.join("/app", os.path.relpath(fluid_data_path, os.getcwd()))
        output_blend_file_in_docker = os.path.join("/app", os.path.relpath(output_blend_file, os.getcwd()))

        # Blender command to run blender_fluid_visualizer.py
        blender_command_args = [
            "blender",
            "--background",
            "--python", blender_script_path_absolute,
            "--", # Separator for arguments to the python script
            fluid_data_path_in_docker, # Arg 1: data_dir
            output_blend_file_in_docker, # Arg 2: output_blend_path
            viz_params_json # Arg 3: viz_params (JSON string)
        ]

        # Execute Blender in headless mode using docker run
        try:
            # Mount the entire project root into the container at /app
            command = [
                "docker", "run", "--rm", "--gpus", "all",
                "-v", f"{os.getcwd()}:/app", # Mount project root
                "-w", "/app", # Set working directory inside container to /app
                "effect_stokes-blender_cuda_runner", # The image name of the blender_runner service
            ] + blender_command_args

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

        print(f"[RenderAgent] Blender file generated: {output_blend_file}")

        print(f"[RenderAgent] Blender file generated: {output_blend_file}")

        # --- GIF Conversion ---
        gif_output_path = output_blend_file.replace(".blend", ".gif")
        image_sequence_dir = os.path.join(self.output_dir, "temp_frames", os.path.basename(output_blend_file).replace(".blend", ""))
        
        # 1. Render frames from Blender
        self._render_frames_to_images(output_blend_file, image_sequence_dir)

        # 2. Use ffmpeg to combine frames into a GIF
        print(f"[RenderAgent] Converting image sequence to GIF: {gif_output_path}")
        try:
            # ffmpeg command to create a GIF from PNG sequence
            # -i: input file pattern
            # -vf: video filter (fps, scale)
            # -loop 0: loop indefinitely
            # -y: overwrite output file without asking
            ffmpeg_command = [
                "ffmpeg",
                "-y", # Overwrite output files without asking
                "-i", os.path.join(image_sequence_dir, "frame_%04d.png"),
                "-vf", "fps=24,scale=512:-1:flags=lanczos", # 24 fps, scale to 512 width, maintain aspect ratio
                "-loop", "0",
                gif_output_path
            ]
            
            print(f"[RenderAgent] Running ffmpeg command: {' '.join(ffmpeg_command)}")
            result = subprocess.run(ffmpeg_command, capture_output=True, text=True, check=True)
            print("[RenderAgent] FFmpeg Stdout:", result.stdout)
            if result.stderr:
                print("[RenderAgent] FFmpeg Stderr:", result.stderr)

            print(f"[RenderAgent] GIF generated: {gif_output_path}")

        except FileNotFoundError:
            print("[RenderAgent] Error: 'ffmpeg' command not found. Make sure FFmpeg is installed and in your PATH.")
            raise
        except subprocess.CalledProcessError as e:
            print(f"[RenderAgent] Error during FFmpeg execution: {e}")
            print("[RenderAgent] FFmpeg Stdout:", e.stdout)
            print("[RenderAgent] FFmpeg Stderr:", e.stderr)
            raise
        except Exception as e:
            print(f"[RenderAgent] An unexpected error occurred during GIF conversion: {e}")
            raise
        finally:
            # Clean up temporary image sequence directory
            if os.path.exists(image_sequence_dir):
                import shutil
                shutil.rmtree(image_sequence_dir)
                print(f"[RenderAgent] Cleaned up temporary image directory: {image_sequence_dir}")

        return {
            "status": "success",
            "message": "Blender file generated and GIF created successfully.",
            "output_blend_file": output_blend_file,
            "output_gif_file": gif_output_path
        }