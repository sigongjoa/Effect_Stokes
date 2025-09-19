
import bpy
import numpy as np
import os
import sys

def visualize_fluid_data(data_dir, output_blend_path):
    """
    Reads fluid simulation data from .npz files and visualizes it in Blender
    using animated arrow objects.

    Args:
        data_dir (str): Path to the directory containing fluid_data_XXXX.npz files.
        output_blend_path (str): Path to save the resulting .blend file.
    """
    # Clear existing scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    scene = bpy.context.scene

    # --- Load Fluid Data ---
    fluid_data_files = sorted([f for f in os.listdir(data_dir) if f.startswith("fluid_data_") and f.endswith(".npz")])
    if not fluid_data_files:
        print(f"Error: No fluid data files found in {data_dir}")
        return

    all_fluid_data = []
    for f_name in fluid_data_files:
        f_path = os.path.join(data_dir, f_name)
        data = np.load(f_path)
        all_fluid_data.append({"u": data["u"], "v": data["v"], "p": data["p"], "x": data["x"], "y": data["y"]})

    if not all_fluid_data:
        print("Error: Failed to load any fluid data.")
        return

    # Get grid info from the first frame
    first_frame_data = all_fluid_data[0]
    x_coords = first_frame_data["x"]
    y_coords = first_frame_data["y"]
    nx = len(x_coords)
    ny = len(y_coords)

    # Set animation frames
    scene.frame_start = 0
    scene.frame_end = len(all_fluid_data) - 1

    # --- Create Arrow Object (Cone) ---
    bpy.ops.mesh.primitive_cone_add(radius1=0.05, depth=0.2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    arrow_obj = bpy.context.object
    arrow_obj.name = "FlowArrow"
    arrow_obj.hide_set(True) # Hide the original, we'll use instances

    # --- Create Grid of Animated Arrows ---
    arrow_instances = []
    # Use a coarser grid for visualization to avoid too many objects
    # Sample every 4th point for a 10x10 grid from 41x41
    sample_step_x = max(1, nx // 10)
    sample_step_y = max(1, ny // 10)

    for i in range(0, ny, sample_step_y):
        for j in range(0, nx, sample_step_x):
            # Create an instance of the arrow object
            instance = bpy.data.objects.new(f"FlowArrow_{i}_{j}", arrow_obj.data)
            scene.collection.objects.link(instance)
            instance.location = (x_coords[j], y_coords[i], 0) # Position in 2D plane
            instance.scale = (0.5, 0.5, 0.5) # Initial scale
            arrow_instances.append({"obj": instance, "grid_x": j, "grid_y": i})

    # --- Animate Arrows ---
    print("Animating arrows...")
    for frame_idx, frame_data in enumerate(all_fluid_data):
        scene.frame_set(frame_idx)
        u_field = frame_data["u"]
        v_field = frame_data["v"]

        for arrow_info in arrow_instances:
            obj = arrow_info["obj"]
            grid_x = arrow_info["grid_x"]
            grid_y = arrow_info["grid_y"]

            vel_u = u_field[grid_y, grid_x]
            vel_v = v_field[grid_y, grid_x]

            # Calculate magnitude for scale
            magnitude = np.sqrt(vel_u**2 + vel_v**2)
            # Calculate angle for rotation (Z-axis rotation for 2D flow)
            angle_rad = np.arctan2(vel_v, vel_u)

            # Set rotation (Euler Z) and scale
            obj.rotation_euler.z = angle_rad
            obj.scale = (0.5 + magnitude * 2, 0.5 + magnitude * 2, 0.5 + magnitude * 2) # Scale based on magnitude

            # Insert keyframes for rotation and scale
            obj.keyframe_insert(data_path="rotation_euler", index=2) # Z-rotation
            obj.keyframe_insert(data_path="scale")

    print("Animation complete.")

    # --- Save Blend File ---
    bpy.ops.wm.save_as_mainfile(filepath=output_blend_path)
    print(f"Blender file saved to {output_blend_path}")


if __name__ == "__main__":
    # Get arguments passed to the script
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if len(args) == 2:
            fluid_data_dir = args[0]
            output_blend_file = args[1]
        else:
            print("Error: Incorrect number of arguments.")
            print("Usage: blender --background --python blender_fluid_visualizer.py -- <fluid_data_directory> <output_blend_file>")
            sys.exit(1)
    else:
        print("Error: Arguments not provided.")
        print("Usage: blender --background --python blender_fluid_visualizer.py -- <fluid_data_directory> <output_blend_file>")
        sys.exit(1)

    visualize_fluid_data(fluid_data_dir, output_blend_file)
