import subprocess
import json
import os
import sys

# Assuming the project root is the current working directory
PROJECT_ROOT = os.getcwd()
MAIN_SCRIPT = os.path.join(PROJECT_ROOT, "src", "main.py")
FLUID_DATA_DIR = os.path.join(PROJECT_ROOT, "workspace", "outputs", "fluid_data")
OUTPUT_BLEND_DIR = os.path.join(PROJECT_ROOT, "workspace", "outputs")

def run_test_case(test_name, prompt, viz_params):
    print(f"\n--- Running Test Case: {test_name} ---")
    output_blend_file = os.path.join(OUTPUT_BLEND_DIR, f"{test_name.replace(' ', '_').lower()}.blend")
    
    # Convert viz_params to JSON string
    viz_params_json = json.dumps(viz_params)

    # Construct the command to run src/main.py
    # This assumes src/main.py can take a prompt and then orchestrate
    # the simulation and visualization, passing viz_params to blender_fluid_visualizer.py
    command = [
        sys.executable, # Use the current python interpreter
        MAIN_SCRIPT,
        "--prompt", prompt,
        "--fluid_data_dir", FLUID_DATA_DIR,
        "--output_blend_file", output_blend_file,
        "--viz_params", viz_params_json
    ]

    print(f"Executing command: {' '.join(command)}")
    try:
        # For a real test, you might want to capture stdout/stderr
        # and check exit codes. For this simulation, we just run it.
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=3600)
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        print(f"Test Case '{test_name}' completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Test Case '{test_name}' FAILED with error:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"Test Case '{test_name}' FAILED: Command timed out after 300 seconds.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: main.py script not found at {MAIN_SCRIPT}. Please ensure src/main.py exists.")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure output directories exist
    os.makedirs(FLUID_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_BLEND_DIR, exist_ok=True)

    # Test Case 1: Basic Getsuga Tenshou Generation
    basic_viz_params = {
        "mesh_params": {"mesh_type": "ribbon", "density_factor": 0.5},
        "material_params": {"base_color": [0.0, 0.0, 0.2], "emission_color": [0.2, 0.2, 0.8], "emission_strength": 5.0, "transparency_alpha": 0.7},
        "freestyle_params": {"enable_freestyle": True, "line_thickness": 2.0, "line_color": [0.0, 0.0, 0.0]},
        "animation_params": {"dissipation_start_frame": 800, "dissipation_end_frame": 1000}
    }
    run_test_case("Basic Getsuga Tenshou", "Generate a Getsuga Tenshou-like fluid VFX.", basic_viz_params)

    # Test Case 2: Parameterized Getsuga Tenshou Generation (Red Color)
    red_viz_params = {
        "mesh_params": {"mesh_type": "ribbon", "density_factor": 0.5},
        "material_params": {"base_color": [0.2, 0.0, 0.0], "emission_color": [0.8, 0.2, 0.2], "emission_strength": 6.0, "transparency_alpha": 0.6},
        "freestyle_params": {"enable_freestyle": True, "line_thickness": 2.5, "line_color": [0.1, 0.0, 0.0]},
        "animation_params": {"dissipation_start_frame": 700, "dissipation_end_frame": 900}
    }
    run_test_case("Red Getsuga Tenshou", "Generate a red Getsuga Tenshou VFX.", red_viz_params)

    # Test Case 3: Dissipation Control (Fast Dissipation)
    fast_dissipation_viz_params = {
        "mesh_params": {"mesh_type": "ribbon", "density_factor": 0.6},
        "material_params": {"base_color": [0.0, 0.0, 0.2], "emission_color": [0.2, 0.2, 0.8], "emission_strength": 5.0, "transparency_alpha": 0.7},
        "freestyle_params": {"enable_freestyle": True, "line_thickness": 2.0, "line_color": [0.0, 0.0, 0.0]},
        "animation_params": {"dissipation_start_frame": 500, "dissipation_end_frame": 600} # Faster dissipation
    }
    run_test_case("Fast Dissipation Getsuga Tenshou", "Generate a Getsuga Tenshou VFX that dissipates quickly.", fast_dissipation_viz_params)

    print("\n--- All Getsuga Tenshou Test Cases Initiated ---")
    print("Please check the 'workspace/outputs/' directory for generated .blend files and GIFs (if main.py handles GIF conversion).")
    print("Review logs for detailed execution results.")
