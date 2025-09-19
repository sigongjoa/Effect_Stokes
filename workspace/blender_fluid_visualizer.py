import bpy
import numpy as np
import os
import sys
import json
import bmesh

def enable_gpu_rendering():
    """Attempts to enable GPU rendering and logs the process for debugging."""
    print("\n[DEBUG] --- GPU Configuration ---")
    try:
        # Ensure render engine is set to CYCLES to access GPU settings
        bpy.context.scene.render.engine = 'CYCLES'
        print("[INFO] Set render engine to CYCLES.")

        # Get Cycles preferences
        cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
        
        print("[INFO] Available compute devices:")
        for device in cycles_prefs.devices:
            print(f"[INFO] - Device: {device.name}, Type: {device.type}")

        # Set compute device type (CUDA is generally well-supported)
        cycles_prefs.compute_device_type = 'CUDA'
        print(f"[INFO] Set compute device type to {cycles_prefs.compute_device_type}.")

        # Enable GPU devices
        gpu_devices = [d for d in cycles_prefs.devices if d.type == 'CUDA'] # Or 'OPTIX'

        if not gpu_devices:
            print("[WARNING] No compatible CUDA GPU found inside the container.")
            print("[WARNING] Falling back to CPU rendering.")
            bpy.context.scene.cycles.device = 'CPU'
        else:
            print("[INFO] Enabling compatible GPU devices...")
            # Unselect all devices first
            for device in cycles_prefs.devices:
                device.use = False
            
            # Enable all found GPUs
            for device in gpu_devices:
                device.use = True
                print(f"[INFO] Enabled GPU device: {device.name}")
            
            bpy.context.scene.cycles.device = 'GPU'
            print("[SUCCESS] GPU rendering is configured.")

    except Exception as e:
        print(f"[ERROR] An error occurred while configuring GPU: {e}")
        print("[WARNING] Could not enable GPU rendering. Falling back to CPU.")
        # Fallback to CPU just in case
        bpy.context.scene.cycles.device = 'CPU'
    
    finally:
        print(f"[DEBUG] Final Cycles device: {bpy.context.scene.cycles.device}")
        print("[DEBUG] --- End of GPU Configuration ---\n")


def create_basic_material(name, base_color_rgb, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create nodes
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')

    # Position nodes
    principled_node.location = -300, 0
    output_node.location = 0, 0

    # Configure Principled BSDF
    principled_node.inputs['Base Color'].default_value = (*base_color_rgb, 1.0)
    principled_node.inputs['Emission'].default_value = (*base_color_rgb, 1.0)
    principled_node.inputs['Emission Strength'].default_value = emission_strength
    principled_node.inputs['Roughness'].default_value = 0.5

    # Links
    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

    return mat

def create_getsuga_mesh(fluid_data_frame, mesh_params):
    print("Creating Getsuga Tenshou mesh from fluid data...")

    x_coords = fluid_data_frame['x']
    y_coords = fluid_data_frame['y']
    pressure = fluid_data_frame['p']

    nx = len(x_coords)
    ny = len(y_coords)

    # Get parameters from mesh_params
    pressure_threshold = mesh_params.get('pressure_threshold', 0.1)
    extrusion_scale = mesh_params.get('extrusion_scale', 0.5)
    scale_x = mesh_params.get('scale_x', 1.0)
    scale_y = mesh_params.get('scale_y', 1.0)

    bm = bmesh.new()
    verts = {}

    # Create vertices
    for i in range(nx):
        for j in range(ny):
            p_val = pressure[j, i] # Assuming pressure is (ny, nx)
            if p_val > pressure_threshold:
                # Scale coordinates and use pressure for Z-height
                x = x_coords[i] * scale_x
                y = y_coords[j] * scale_y
                z = p_val * extrusion_scale
                vert = bm.verts.new((x, y, z))
                verts[(i, j)] = vert
            else:
                verts[(i, j)] = None # Mark as no vertex created

    # Create faces
    for i in range(nx - 1):
        for j in range(ny - 1):
            v1 = verts.get((i, j))
            v2 = verts.get((i + 1, j))
            v3 = verts.get((i + 1, j + 1))
            v4 = verts.get((i, j + 1))

            # Only create a face if all 4 vertices exist
            if all([v1, v2, v3, v4]):
                try:
                    bm.faces.new((v1, v2, v3, v4))
                except ValueError:
                    # Handle cases where face creation might fail (e.g., non-planar quads)
                    # For simplicity, we'll just skip for now. More robust handling might be needed.
                    pass

    # Create a new mesh data block
    mesh_data = bpy.data.meshes.new("GetsugaMesh")
    bm.to_mesh(mesh_data)
    bm.free()

    return mesh_data

def create_getsuga_material(material_params):
    # Placeholder for Getsuga Tenshou material creation
    print("Creating Getsuga Tenshou material...")
    mat = bpy.data.materials.new(name="GetsugaMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Principled BSDF
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    nodes.active = principled_node
    principled_node.location = -300, 0

    # Material Output
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = 0, 0

    # Links
    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

    # Configure based on material_params (simplified for placeholder)
    base_color = material_params.get("base_color", (0.0, 0.0, 0.2))
    emission_color = material_params.get("emission_color", (0.2, 0.2, 0.8))
    emission_strength = material_params.get("emission_strength", 5.0)
    transparency_alpha = material_params.get("transparency_alpha", 0.7)

    principled_node.inputs['Base Color'].default_value = (*base_color, 1.0)
    principled_node.inputs['Emission'].default_value = (*emission_color, 1.0)
    principled_node.inputs['Emission Strength'].default_value = emission_strength
    principled_node.inputs['Alpha'].default_value = transparency_alpha # For transparency

    return mat

def configure_freestyle(freestyle_params):
    # Placeholder for Freestyle configuration
    print("Configuring Freestyle...")
    scene = bpy.context.scene
    scene.render.use_freestyle = False
    if scene.render.use_freestyle:
        # Basic configuration
        scene.view_layers["ViewLayer"].use_freestyle = True
        # Add a line set
        for ls in list(scene.view_layers["ViewLayer"].freestyle_settings.linesets):
            scene.view_layers["ViewLayer"].freestyle_settings.linesets.remove(ls)
            
        lineset = scene.view_layers["ViewLayer"].freestyle_settings.linesets.new("GetsugaLineSet")
        
        lineset.select_by_edge_types = True
        lineset.select_crease = True
        lineset.select_border = True
        lineset.select_material_boundary = True
        
        lineset.linestyle.thickness = freestyle_params.get("line_thickness", 2.0)
        line_color = freestyle_params.get("line_color", (0.0, 0.0, 0.0))
        lineset.linestyle.color = line_color

def animate_getsuga_vfx(all_fluid_data, mesh_objects, material_params, animation_params):
    print("Animating Getsuga Tenshou VFX...")
    scene = bpy.context.scene
    
    dissipation_start_frame = animation_params.get("dissipation_start_frame", scene.frame_end - 200)
    dissipation_end_frame = animation_params.get("dissipation_end_frame", scene.frame_end)

    # Get the shared Getsuga material
    getsuga_material = bpy.data.materials.get("GetsugaMaterial")
    if not getsuga_material or not getsuga_material.use_nodes:
        print("Error: GetsugaMaterial not found or does not use nodes. Cannot animate material.")
        return

    principled_node = getsuga_material.node_tree.nodes.get('Principled BSDF')
    if not principled_node:
        print("Error: Principled BSDF node not found in GetsugaMaterial. Cannot animate material.")
        return

    for frame_idx, frame_data in enumerate(all_fluid_data):
        scene.frame_set(frame_idx)
        
        # Make the current frame's mesh visible
        if frame_idx < len(mesh_objects): # Ensure index is within bounds
            obj = mesh_objects[frame_idx]
            obj.hide_set(False)
            obj.hide_render = False
            obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx)
            obj.keyframe_insert(data_path="hide_render", frame=frame_idx)

        # Animate material properties for dissipation
        if dissipation_start_frame <= frame_idx <= dissipation_end_frame:
            factor = (frame_idx - dissipation_start_frame) / (dissipation_end_frame - dissipation_start_frame)
            
            # Fade out emission strength
            current_emission_strength = material_params.get("emission_strength", 5.0) * (1 - factor)
            principled_node.inputs['Emission Strength'].default_value = current_emission_strength
            principled_node.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=frame_idx)
            
            # Fade out transparency (become more transparent)
            current_alpha = material_params.get("transparency_alpha", 0.7) * (1 - factor)
            principled_node.inputs['Alpha'].default_value = current_alpha
            principled_node.inputs['Alpha'].keyframe_insert(data_path="default_value", frame=frame_idx)

    print("Getsuga Tenshou VFX animation complete.")

def visualize_fluid_data(data_dir, output_blend_path, viz_params):
    """
    Reads fluid simulation data from .npz files and visualizes it in Blender
    to create a stylized "Getsuga Tenshou" VFX.

    Args:
        data_dir (str): Path to the directory containing fluid_data_XXXX.npz files.
        output_blend_path (str): Path to save the resulting .blend file.
        viz_params (dict): Dictionary of visualization parameters, including:
                           mesh_params, material_params, freestyle_params, animation_params.
    """
    print("\n--- Starting Blender Visualization ---")
    print(f"[INFO] Data directory: {data_dir}")
    print(f"[INFO] Output .blend file: {output_blend_path}")
    print(f"[INFO] Received viz_params: {json.dumps(viz_params, indent=2)}")

    # Enable GPU rendering
    enable_gpu_rendering()

    # Clear existing scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    scene = bpy.context.scene

    # --- Visualization Parameters from viz_params ---
    mesh_params = viz_params.get("mesh_params", {})
    material_params = viz_params.get("material_params", {})
    freestyle_params = viz_params.get("freestyle_params", {})
    animation_params = viz_params.get("animation_params", {})

    # --- Load Fluid Data ---
    print("[INFO] Loading fluid data files...")
    fluid_data_files = sorted([f for f in os.listdir(data_dir) if f.startswith("fluid_data_") and f.endswith(".npz")])
    if not fluid_data_files:
        print(f"[ERROR] No fluid data files found in {data_dir}")
        return

    print(f"[INFO] Found {len(fluid_data_files)} fluid data files.")

    all_fluid_data = []
    for f_name in fluid_data_files:
        f_path = os.path.join(data_dir, f_name)
        data = np.load(f_path)
        all_fluid_data.append({"u": data["u"], "v": data["v"], "p": data["p"], "x": data["x"], "y": data["y"]})

    if not all_fluid_data:
        print("[ERROR] Failed to load any fluid data.")
        return

    # Get grid info from the first frame (still useful for domain size)
    first_frame_data = all_fluid_data[0]
    x_coords = first_frame_data["x"]
    y_coords = first_frame_data["y"]
    nx = len(x_coords)
    ny = len(y_coords)
    print(f"[INFO] Fluid grid resolution: {nx}x{ny}")

    # Set animation frames
    scene.render.fps = 24
    scene.frame_start = 0
    # Cap the animation at 3 seconds (72 frames at 24fps) for testing
    max_frames = 3 * 24
    scene.frame_end = min(len(all_fluid_data) - 1, max_frames)
    print(f"[INFO] Scene FPS set to {scene.render.fps}.")
    print(f"[INFO] Set animation frame range: {scene.frame_start} to {scene.frame_end} (capped at {max_frames} frames).")


    # --- Getsuga Tenshou VFX Implementation ---
    # 1. Create stylized material
    getsuga_material = create_getsuga_material(material_params)

    # 2. Configure Freestyle for outlines
    configure_freestyle(freestyle_params)

    # 3. Generate meshes for each frame and link material
    print("[INFO] Generating meshes for each frame...")
    mesh_objects = []
    for frame_idx, frame_data in enumerate(all_fluid_data):
        print(f"[DEBUG] Processing frame {frame_idx}...")
        scene.frame_set(frame_idx)
        # Ensure clean selection before creating objects
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = None

        mesh_data = create_getsuga_mesh(frame_data, mesh_params)
        mesh_obj = bpy.data.objects.new(f"GetsugaVFX_Frame_{frame_idx:04d}", mesh_data)
        scene.collection.objects.link(mesh_obj)
        
        if getsuga_material:
            if mesh_obj.data.materials:
                mesh_obj.data.materials[0] = getsuga_material
            else:
                mesh_obj.data.materials.append(getsuga_material)
        
        # Hide all meshes by default, animation will control visibility
        mesh_obj.hide_set(True)
        mesh_obj.hide_render = True
        mesh_obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx)
        mesh_obj.keyframe_insert(data_path="hide_render", frame=frame_idx)

        mesh_objects.append(mesh_obj)
    print(f"[INFO] Generated {len(mesh_objects)} mesh objects.")
    
    # 4. Animate meshes and material properties
    animate_getsuga_vfx(all_fluid_data, mesh_objects, material_params, animation_params)

    # --- Setup Camera and Light (Basic) ---
    print("[INFO] Setting up camera and lights...")
    # Remove default cube
    if "Cube" in bpy.data.objects:
        bpy.data.objects["Cube"].select_set(True)
        bpy.ops.object.delete()

    # Add a camera
    bpy.ops.object.camera_add(location=(1.0, 1.0, 5.0))
    camera = bpy.context.object
    scene.camera = camera
    camera.rotation_euler = (0, 0, 0) # Look straight down

    # Add a light
    bpy.ops.object.light_add(type='SUN', location=(1.0, 1.0, 10.0))
    light = bpy.context.object
    light.data.energy = 2.0

    # Add a floor plane
    bpy.ops.mesh.primitive_plane_add(size=5, enter_editmode=False, align='WORLD', location=(1.0, 1.0, -0.1))
    floor_obj = bpy.context.object
    floor_obj.name = "Floor"
    floor_mat = create_basic_material("FloorMaterial", (0.2, 0.2, 0.2), 0.0)
    if floor_obj.data.materials:
        floor_obj.data.materials[0] = floor_mat
    else:
        floor_obj.data.materials.append(floor_mat)

    # --- Camera Animation (Simple Orbit) ---
    print("[INFO] Setting up camera animation...")
    camera_orbit_radius = 6.0
    camera_orbit_height = 3.0
    camera_target = (1.0, 1.0, 0.0) # Center of the fluid domain

    # Helper function to convert direction vector to quaternion (look_at equivalent)
    def direction_to_quaternion(direction_vector, up_axis='Y'):
        from mathutils import Vector
        # Ensure direction is normalized
        direction_vector = Vector(direction_vector).normalized()
        # Use to_track_quat to get the rotation to point along the direction vector
        # 'Z' is the forward axis for the camera, 'Y' is the up axis
        return direction_vector.to_track_quat('Z', up_axis)

    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        angle = (frame / (scene.frame_end - scene.frame_start + 1)) * 2 * np.pi
        cam_x = camera_target[0] + camera_orbit_radius * np.cos(angle)
        cam_y = camera_target[1] + camera_orbit_radius * np.sin(angle)
        cam_z = camera_orbit_height

        camera.location = (cam_x, cam_y, cam_z)
        # Point camera to target
        direction = np.array(camera_target) - np.array(camera.location)
        rot_quat = direction_to_quaternion(direction)
        camera.rotation_mode = 'QUATERNION'
        camera.rotation_quaternion = rot_quat

        camera.keyframe_insert(data_path="location")
        camera.keyframe_insert(data_path="rotation_quaternion")

    print("Camera animation complete.")

    # --- Save Blend File ---
    print(f"[INFO] Saving final .blend file to {output_blend_path}...")
    bpy.ops.wm.save_as_mainfile(filepath=output_blend_path)
    print(f"Blender file saved to {output_blend_path}")
    print("--- Blender Visualization Finished ---")


if __name__ == "__main__":
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if len(args) == 3:
            fluid_data_dir = args[0]
            output_blend_file = args[1]
            viz_params_json = args[2]
            viz_params = json.loads(viz_params_json)
        else:
            print("Error: Incorrect number of arguments.")
            print("Usage: blender --background --python blender_fluid_visualizer.py -- <fluid_data_directory> <output_blend_file> <viz_params_json>")
            sys.exit(1)
    else:
        print("Error: Arguments not provided.")
        print("Usage: blender --background --python blender_fluid_visualizer.py -- <fluid_data_directory> <output_blend_file> <viz_params_json>")
        sys.exit(1)

    visualize_fluid_data(fluid_data_dir, output_blend_file, viz_params)
