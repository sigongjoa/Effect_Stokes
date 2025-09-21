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
                print(output.strip()) # Print live output
                lines.append(output)
                
        rc = process.poll()
        full_output = "".join(lines)

        if rc != 0:
            # The output was already printed live, so just raise the error
            raise subprocess.CalledProcessError(rc, cmd, output=full_output)
            
        return full_output

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        # The output was already printed, so no need to print e.stdout again
        raise

def main():
    print("--- Step 1: Running Full Simulation ---")
    simulation_output = run_command([sys.executable, RUN_SIMULATION_SCRIPT], cwd=PROJECT_ROOT)

    # Parse simulation output to get necessary parameters for Blender visualization
    fluid_data_path = None
    inferred_visualization_params_str = None
    blender_visualizer_cmd_str = None
    
    # Look for the line containing the Blender visualizer command
    for line in simulation_output.splitlines():
        if "blender --background --python" in line and BLENDER_VISUALIZER_SCRIPT in line:
            blender_visualizer_cmd_str = line.strip()
            break
    
    if not blender_visualizer_cmd_str:
        print("Error: Could not find Blender visualizer command in simulation output.")
        sys.exit(1)

    # Extract fluid_data_path and inferred_visualization_params from the command string
    # The command string is like: blender --background --python ... -- <fluid_data_path> <output_blend_path> <inferred_visualization_params_json>
    parts = blender_visualizer_cmd_str.split(" -- ")
    if len(parts) < 2:
        print("Error: Malformed Blender visualizer command string.")
        sys.exit(1)
    
    blender_args_after_double_dash = parts[1].split(maxsplit=2)
    if len(blender_args_after_double_dash) < 3:
        print("Error: Not enough arguments after -- in Blender visualizer command.")
        sys.exit(1)

    fluid_data_path = blender_args_after_double_dash[0]
    output_blend_file = blender_args_after_double_dash[1]
    inferred_visualization_params_str = blender_args_after_double_dash[2] # This is a JSON string

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
        inferred_visualization_params_str
    ]
    run_command(blender_oneshot_cmd, cwd=PROJECT_ROOT)

    print("\n--- Full pipeline completed successfully! ---")
    print(f"Rendered frames are in: {os.path.dirname(render_output_path)}")

if __name__ == "__main__":
    main()