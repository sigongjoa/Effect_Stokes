import sys
import os

# Add the project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import subprocess
import os
import json
import threading
import logging
import re
from src.param_evaluator import ParamEvaluator
import tempfile
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from src.fluid_simulator import FluidSimulator

# Initialize ParamEvaluator
param_evaluator = ParamEvaluator()

# Configure logging
log_file = os.path.join(os.path.dirname(__file__), 'server.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app) # Enable CORS for all origins
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global variable to store the pipeline process
pipeline_process = None

# Utility function for parameter validation (detailed)
def _validate_type(value, expected_type, param_name):
    if expected_type == float and isinstance(value, int):
        return True, None # Allow int to be treated as float
    if not isinstance(value, expected_type):
        # If expected type is float/int, but value is string, try to evaluate it as a function
        if (expected_type == float or expected_type == int) and isinstance(value, str):
            try:
                # Temporarily evaluate at t=0 to check if it's a valid expression
                param_evaluator.evaluate(value, t=0)
                return True, None
            except ValueError:
                return False, f"Parameter '{param_name}' is a string but not a valid mathematical expression."
        return False, f"Parameter '{param_name}' must be of type {expected_type.__name__}"
    return True, None

def _validate_range(value, min_val, max_val, param_name):
    # If value is a string (function), we can't validate its range directly here.
    # The range validation will happen during evaluation at each timestep.
    if isinstance(value, str):
        return True, None
    if not (min_val <= value <= max_val):
        return False, f"Parameter '{param_name}' must be between {min_val} and {max_val}"
    return True, None

def _validate_list_length(value, expected_len, param_name):
    if not isinstance(value, list) or len(value) != expected_len:
        return False, f"Parameter '{param_name}' must be a list of length {expected_len}"
    return True, None

def validate_params(params):
    if not isinstance(params, dict):
        return False, "Parameters must be a dictionary"

    sim_params = params.get("simulation_params")
    viz_params = params.get("visualization_params")

    if not isinstance(sim_params, dict) or not isinstance(viz_params, dict):
        return False, "simulation_params and visualization_params must be dictionaries"

    # Simulation Parameters Validation
    sim_validation_rules = {
        "grid_resolution": {"type": list, "len": 2, "item_type": int, "min_item": 20, "max_item": 200},
        "time_steps": {"type": int, "min": 10, "max": 2000},
        "viscosity": {"type": float, "min": 0.001, "max": 0.1},
        "initial_shape_type": {"type": str, "allowed": ["vortex", "crescent", "circle_burst"]},
        "initial_shape_position": {"type": list, "len": 2, "item_type": float, "min_item": 0.0, "max_item": 2.0},
        "initial_shape_size": {"type": float, "min": 0.1, "max": 1.0},
        "initial_velocity": {"type": list, "len": 2, "item_type": float, "min_item": -5.0, "max_item": 5.0},
        "boundary_conditions": {"type": str, "allowed": ["no_slip_walls"]}, # Currently fixed
        "vortex_strength": {"type": float, "min": 0.0, "max": 5.0},
        "source_strength": {"type": float, "min": 0.0, "max": 5.0},
    }

    for param, rules in sim_validation_rules.items():
        value = sim_params.get(param)
        if value is None:
            continue

        is_valid, msg = _validate_type(value, rules["type"], param)
        if not is_valid: return False, msg

        if rules["type"] == list:
            is_valid, msg = _validate_list_length(value, rules["len"], param)
            if not is_valid: return False, msg
            for item in value:
                # For list items, if they are strings, they are not expected to be functions
                is_valid, msg = _validate_type(item, rules["item_type"], f"{param} item")
                if not is_valid: return False, msg
                is_valid, msg = _validate_range(item, rules["min_item"], rules["max_item"], f"{param} item")
                if not is_valid: return False, msg
        elif rules["type"] in [int, float]:
            # If it's a string, _validate_type already checked if it's a valid expression
            # Range check for string expressions is skipped here, done at evaluation time.
            if not isinstance(value, str):
                is_valid, msg = _validate_range(value, rules["min"], rules["max"], param)
                if not is_valid: return False, msg
        elif rules["type"] == str:
            if "allowed" in rules and value not in rules["allowed"]:
                return False, f"Parameter '{param}' must be one of {rules['allowed']}"
    
    # Visualization Parameters Validation
    viz_validation_rules = {
        "arrow_color": {"type": list, "len": 3, "item_type": float, "min_item": 0.0, "max_item": 1.0},
        "arrow_scale_factor": {"type": float, "min": 0.1, "max": 10.0},
        "arrow_density": {"type": int, "min": 1, "max": 50},
        "emission_strength": {"type": float, "min": 0.0, "max": 100.0},
        "transparency_alpha": {"type": float, "min": 0.0, "max": 1.0},
        "render_samples": {"type": int, "min": 1, "max": 4096},
    }

    for param, rules in viz_validation_rules.items():
        value = viz_params.get(param)
        if value is None:
            continue

        is_valid, msg = _validate_type(value, rules["type"], param)
        if not is_valid: return False, msg

        if rules["type"] == list:
            is_valid, msg = _validate_list_length(value, rules["len"], param)
            if not is_valid: return False, msg
            for item in value:
                is_valid, msg = _validate_type(item, rules["item_type"], f"{param} item")
                if not is_valid: return False, msg
                is_valid, msg = _validate_range(item, rules["min_item"], rules["max_item"], f"{param} item")
                if not is_valid: return False, msg
        elif rules["type"] in [int, float]:
            if not isinstance(value, str):
                is_valid, msg = _validate_range(value, rules["min"], rules["max"], param)
                if not is_valid: return False, msg
        elif rules["type"] == str:
            if "allowed" in rules and value not in rules["allowed"]:
                return False, f"Parameter '{param}' must be one of {rules['allowed']}"

    return True, None


# API Endpoint to run the pipeline
@app.route('/api/run_pipeline', methods=['POST'])
def run_pipeline():
    global pipeline_process
    if pipeline_process and pipeline_process.poll() is None:
        return jsonify({"status": "error", "message": "Pipeline is already running."}), 400

    params = request.get_json()
    is_valid, error_msg = validate_params(params)
    if not is_valid:
        return jsonify({"status": "error", "message": error_msg}), 400

    # Extract params for the pipeline script
    simulation_params = params.get("simulation_params", {})
    visualization_params = params.get("visualization_params", {})

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    pipeline_script = os.path.join(project_root, 'src', 'run_full_pipeline.py')
    venv_python = os.path.join(project_root, 'venv', 'bin', 'python3')

    # Construct the command to run the pipeline
    command = [
        venv_python,
        pipeline_script,
        json.dumps(simulation_params), # Pass simulation params as JSON string
        json.dumps(visualization_params) # Pass visualization params as JSON string
    ]

    def run_in_thread(cmd):
        global pipeline_process
        try:
            socketio.emit('pipeline_status', {"type": "status", "status": "running", "message": "Pipeline started.", "current_step": "initial"})
            pipeline_process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, # Decode stdout/stderr as text
                bufsize=1, # Line-buffered
                universal_newlines=True # Ensure cross-platform line endings
            )

            for line in iter(pipeline_process.stdout.readline, ''):
                stripped_line = line.strip()
                socketio.emit('pipeline_log', {"type": "log", "message": stripped_line})
                logger.info(f"PIPELINE: {stripped_line}") # Log pipeline output
                frame = 0
                sample = 0
                total_samples = 0
                percentage = 0.0
                # Basic progress parsing (can be enhanced)
                if "Fra:" in line and "Mem:" in line:
                    match = re.search(r"Fra:(\d+).*Sample (\d+)/(\d+)", line)
                    if match:
                        frame = int(match.group(1))
                        sample = int(match.group(2))
                        total_samples = int(match.group(3))
                        percentage = (sample / total_samples) * 100
            socketio.emit('pipeline_status', {
                            "type": "status", 
                            "status": "running", 
                            "message": f"Rendering frame {frame}...", 
                            "current_step": "rendering",
                            "progress": percentage,
                            "current_frame": frame,
                            "total_samples": total_samples,
                            "current_sample": sample
                        })

            pipeline_process.wait()
            if pipeline_process.returncode == 0:
                # Assuming run_full_pipeline.py prints the GIF path as the last line
                # Or we can infer it based on the blend_file_name_without_ext
                output_dir_name = "my_custom_fluid_vfx" # Default name from pipeline
                output_frames_path = f"/outputs/temp_frames/{output_dir_name}"
                gif_output_path = f"/outputs/{output_dir_name}.gif"
                full_gif_url = f"http://localhost:5000{gif_output_path}"
                socketio.emit('pipeline_status', {"type": "status", "status": "completed", "message": "Pipeline completed successfully.", "current_step": "completed", "output_url": output_frames_path, "gif_url": full_gif_url})
            else:
                socketio.emit('pipeline_status', {"type": "status", "status": "failed", "message": f"Pipeline failed with exit code {pipeline_process.returncode}", "current_step": "failed"})
        except Exception as e:
            socketio.emit('pipeline_status', {"type": "status", "status": "failed", "message": f"An error occurred: {e}", "current_step": "failed"})
        finally:
            pipeline_process = None

    thread = threading.Thread(target=run_in_thread, args=(command,))
    thread.daemon = True # Allow main program to exit even if thread is running
    thread.start()

    return jsonify({"status": "success", "message": "Pipeline execution initiated."}), 200

@app.route('/api/get_llm_inferred_params', methods=['POST'])
def get_llm_inferred_params():
    params = request.get_json()
    effect_description = params.get("effect_description", {"vfx_type": "swirling vortex", "style": "blue liquid"})

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    venv_python = os.path.join(project_root, 'venv', 'bin', 'python3')

    command = [
        venv_python,
        "-m", "src.run_full_simulation", # Run as a module
        "--infer_only",
        json.dumps(effect_description) # Pass effect_description as JSON string
    ]

    try:
        # Get the current environment and set PYTHONPATH for the subprocess
        env = os.environ.copy()
        env['PYTHONPATH'] = project_root

        process = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
            env=env # Pass the modified environment
        )
        logger.info(f"stdout from simulation script: {process.stdout}")
        logger.error(f"stderr from simulation script: {process.stderr}")
        output = json.loads(process.stdout)
        return jsonify({
            "status": "success",
            "simulation_params": output.get("simulation_params"),
            "visualization_params": output.get("visualization_params")
        }), 200
    except subprocess.CalledProcessError as e:
        logger.error(f"Error inferring parameters: {e.stderr}")
        return jsonify({"status": "error", "message": f"Failed to infer parameters: {e.stderr}"}), 500
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from simulation script: {e}")
        return jsonify({"status": "error", "message": "Failed to parse parameters from simulation script."}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

def _create_frame_image(u, v, x, y, frame_idx) -> str:
    """
    Generates a single frame image (quiver plot) from fluid data and returns it as a base64 string.
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Downsample the data for a clearer plot
    step = max(1, len(x) // 20) # Aim for about 20 arrows
    x_s, y_s = x[::step], y[::step]
    u_s, v_s = u[::step, ::step], v[::step, ::step]
    X_s, Y_s = np.meshgrid(x_s, y_s)

    ax.quiver(X_s, Y_s, u_s.T, v_s.T, scale=1, scale_units='xy') # Transpose u and v for correct orientation
    ax.set_aspect('equal')
    ax.set_title(f'Fluid Velocity Preview - Frame {frame_idx}')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    buf = io.BytesIO()
    plt.savefig(buf, bbox_inches='tight', format='png')
    plt.close(fig)
    buf.seek(0)
    
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.route('/api/run_preview', methods=['POST'])
def run_preview():
    params = request.get_json()
    sim_params_input = params.get("simulation_params", {})

    is_valid, error_msg = validate_params({
        "simulation_params": sim_params_input,
        "visualization_params": {} 
    })
    if not is_valid:
        if "visualization_params" not in error_msg:
             return jsonify({"status": "error", "message": error_msg}), 400

    output_dir = tempfile.mkdtemp(prefix="preview_sim_")
    logger.info(f"Created temporary directory for preview: {output_dir}")

    try:
        simulator = FluidSimulator()
        preview_settings = params.get("preview_settings", {})
        requested_frames = preview_settings.get("duration_frames", 30)
        num_frames_for_preview = requested_frames # No cap on frames
        sim_params_input['time_steps'] = num_frames_for_preview

        result = simulator.run_simulation(sim_params_input, output_dir)

        if result["status"] != "success":
            return jsonify({"status": "error", "message": result.get("message", "Simulation failed.")}), 500

        b64_images = []
        for i in range(num_frames_for_preview):
            frame_fluid_data_path = os.path.join(output_dir, f"fluid_data_frame_{i:04d}.npz")
            if not os.path.exists(frame_fluid_data_path):
                logger.warning(f"Fluid data for frame {i} not found at {frame_fluid_data_path}. Skipping frame.")
                continue
            
            data = np.load(frame_fluid_data_path)
            u, v, x, y = data['u'], data['v'], data['x'], data['y']
            
            b64_image = _create_frame_image(u, v, x, y, i)
            b64_images.append(b64_image)

        return jsonify({
            "status": "success",
            "message": "Preview frames generated successfully.",
            "preview_data": {"frames": b64_images, "total_frames": len(b64_images)}
        }), 200

    except ValueError as e:
        logger.error(f"Parameter evaluation error during preview: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"An unexpected error occurred during preview: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            logger.info(f"Removed temporary directory: {output_dir}")

# API Endpoint to stop the pipeline
@app.route('/api/stop_pipeline', methods=['POST'])
def stop_pipeline():
    global pipeline_process
    if pipeline_process and pipeline_process.poll() is None:
        try:
            # Terminate the process group to ensure all child processes are killed
            os.killpg(os.getpgid(pipeline_process.pid), subprocess.signal.SIGTERM)
            pipeline_process.wait(timeout=5) # Give it some time to terminate
            socketio.emit('pipeline_status', {"type": "status", "status": "stopped", "message": "Pipeline stopped by user.", "current_step": "stopped"})
            return jsonify({"status": "success", "message": "Pipeline stopped."}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to stop pipeline: {e}"}), 500
    else:
        return jsonify({"status": "info", "message": "No pipeline is currently running."}), 200

# Serve static files (rendered images)
@app.route('/outputs/<path:filename>')
def serve_outputs(filename):
    # Ensure the path is secure and within the intended outputs directory
    # This serves files from the project's root outputs directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    outputs_dir = os.path.join(project_root, 'outputs')
    return send_from_directory(outputs_dir, filename)


if __name__ == '__main__':
    # Use eventlet for SocketIO async mode
    try:
        import eventlet
        eventlet.monkey_patch()
    except ImportError:
        print("Eventlet not found. Falling back to default threading mode for SocketIO.")
        print("Real-time performance might be affected. Install with: pip install eventlet")

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
