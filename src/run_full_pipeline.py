import subprocess
import json
import os
import sys

# Define absolute paths
PROJECT_ROOT = "/mnt/d/progress/Effect_Stokes"
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
RUN_SIMULATION_SCRIPT = os.path.join(SRC_DIR, "run_full_simulation.py")
BLENDER_VISUALIZER_SCRIPT = os.path.join(SRC_DIR, "blender_fluid_visualizer.py")
VERIFY_BLEND_SCRIPT = os.path.join(PROJECT_ROOT, "verify_blend_file.py")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

# TODO: Set your Blender executable path here
BLENDER_EXECUTABLE_PATH = "/snap/bin/blender"

def run_command(cmd, cwd=None):
    print(f"Executing: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        
        lines = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip()) # Always print live output for debugging
                lines.append(output)
                
        rc = process.poll()
        full_output = "".join(lines)

        if rc != 0:
            raise subprocess.CalledProcessError(rc, cmd, output=full_output)
            
        return full_output

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        # The output was already printed, so no need to print e.stdout again
        raise

def create_gif_from_frames(input_frame_path, output_gif_path, fps=15):
    print(f"\n--- Step 7: Creating GIF from frames ---")
    # FFmpeg command to create a GIF from PNG sequence
    # -i: input file pattern (e.g., frame_%04d.png)
    # -vf: video filters (scale, fps, palettegen/paletteuse for optimized GIF)
    # -loop 0: loop indefinitely
    # -y: overwrite output file without asking
    gif_command = [
        "ffmpeg",
        "-y", # Overwrite output file without asking
        "-i", input_frame_path.replace("frame_####", "frame_%04d.png"),
        "-filter_complex", "fps={},scale=512:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse".format(fps),
        "-loop", "0",
        output_gif_path
    ]
    try:
        run_command(gif_command, cwd=PROJECT_ROOT) # Use run_command to execute FFmpeg
        print(f"GIF created successfully at: {output_gif_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating GIF: {e}")
        raise

def main(simulation_params_json=None, visualization_params_json=None):
    print("--- Step 1: Running Full Simulation ---")
    
    # Pass simulation_params_json to run_full_simulation.py
    sim_command = [sys.executable, RUN_SIMULATION_SCRIPT]
    if simulation_params_json:
        sim_command.append(simulation_params_json)
    else:
        sim_command.append("{}") # Pass empty JSON if no params provided
    if visualization_params_json:
        sim_command.append(visualization_params_json)
    else:
        sim_command.append("{}") # Pass empty JSON if no params provided
    simulation_output = run_command(sim_command, cwd=PROJECT_ROOT)

    # Parse simulation output to get necessary parameters for Blender visualization
    try:
        result_data = json.loads(simulation_output)
        fluid_data_path = result_data.get("output_data_path")
        # The simulation_params and visualization_params returned by run_full_simulation.py
        # are the *original* (potentially function-based) ones passed in.
        # We need to pass these raw strings to blender_oneshot_cmd.
        simulation_params_to_use_str = json.dumps(result_data.get("simulation_params", {}))
        visualization_params_to_use_str = json.dumps(result_data.get("visualization_params", {}))

    except json.JSONDecodeError as e:
        print(f"Error parsing simulation result JSON: {e}")
        sys.exit(1)
    
    if not fluid_data_path:
        print("Error: Could not parse fluid data path from simulation output.")
        sys.exit(1)

    # Ensure output directory for frames exists
    blend_file_name_without_ext = "my_custom_fluid_vfx" # Set a base name
    render_output_path = os.path.join(OUTPUTS_DIR, "temp_frames", blend_file_name_without_ext, "frame_####")
    os.makedirs(os.path.dirname(render_output_path), exist_ok=True)

    print("\n--- Step 2: Blender Processing (Create, Verify, Render) ---")
    oneshot_script_path = os.path.join(PROJECT_ROOT, "run_blender_oneshot.py")
    blender_oneshot_cmd = [
        BLENDER_EXECUTABLE_PATH,
        "--background",
        "--python", oneshot_script_path,
        "--",
        fluid_data_path,
        render_output_path,
        simulation_params_to_use_str, # Pass raw sim params
        visualization_params_to_use_str # Pass raw viz params
    ]
    run_command(blender_oneshot_cmd, cwd=PROJECT_ROOT)

    # --- GIF Creation ---
    gif_output_path = os.path.join(OUTPUTS_DIR, f"{blend_file_name_without_ext}.gif")
    create_gif_from_frames(render_output_path, gif_output_path)

    print("\n--- Full pipeline completed successfully! ---")
    print(f"Rendered frames are in: {os.path.dirname(render_output_path)}")
    print(f"Generated GIF is at: {gif_output_path}")

if __name__ == "__main__":
    # Parse parameters from command line when run directly
    sim_params_json_arg = "{}"
    viz_params_json_arg = "{}"
    if len(sys.argv) > 1:
        sim_params_json_arg = sys.argv[1]
    if len(sys.argv) > 2:
        viz_params_json_arg = sys.argv[2]
    main(sim_params_json_arg, viz_params_json_arg)