import bpy
import numpy as np
import os
import json
import sys

# Add the src directory to the Python path to import ParamEvaluator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from param_evaluator import ParamEvaluator

class BlenderFluidVisualizer:
    def __init__(self):
        self.param_evaluator = ParamEvaluator()

    def _clear_scene(self):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        # Create a new camera
        bpy.ops.object.camera_add(location=(0, -5, 2))
        bpy.context.scene.camera = bpy.context.object

        # Create a new light (Sun lamp)
        bpy.ops.object.light_add(type='SUN', location=(0, 0, 5))
        bpy.context.object.data.energy = 3.0

    def setup_scene_and_render(self, fluid_data_path, render_output_path, simulation_params_json, visualization_params_json):
        self._clear_scene()

        # Parse JSON strings into dictionaries
        simulation_params = json.loads(simulation_params_json)
        visualization_params = json.loads(visualization_params_json)

        # Get total frames from simulation parameters
        total_frames = simulation_params.get("time_steps", 30)
        bpy.context.scene.frame_end = total_frames - 1

        # Set render settings
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = render_output_path
        bpy.context.scene.render.resolution_x = 1080
        bpy.context.scene.render.resolution_y = 1080
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = visualization_params.get("render_samples", 128)

        # Create a collection for fluid arrows
        fluid_collection = bpy.data.collections.new("FluidArrows")
        bpy.context.scene.collection.children.link(fluid_collection)

        # Create a base arrow mesh (cone for simplicity)
        bpy.ops.mesh.primitive_cone_add(radius1=0.05, depth=0.2, enter_editmode=False, align='WORLD', location=(0,0,0))
        base_arrow = bpy.context.object
        base_arrow.name = "BaseArrow"
        base_arrow.hide_render = True # Hide the base arrow, we'll instance it

        # Create a material for the arrows
        arrow_material = bpy.data.materials.new(name="ArrowMaterial")
        arrow_material.use_nodes = True
        bsdf = arrow_material.node_tree.nodes["Principled BSDF"]
        # Set base color (will be updated per frame)
        bsdf.inputs['Base Color'].default_value = (0.0, 0.0, 0.8, 1)
        # Set emission (will be updated per frame)
        emission = arrow_material.node_tree.nodes.new(type='ShaderNodeEmission')
        emission.inputs['Color'].default_value = (0.0, 0.0, 0.8, 1)
        emission.inputs['Strength'].default_value = 50.0
        arrow_material.node_tree.links.new(emission.outputs['Emission'], bsdf.inputs['Emission'])
        # Set transparency
        bsdf.inputs['Alpha'].default_value = visualization_params.get("transparency_alpha", 0.1)
        arrow_material.blend_method = 'BLEND'
        arrow_material.shadow_method = 'NONE'

        # Link material to base arrow
        if base_arrow.data.materials:
            base_arrow.data.materials[0] = arrow_material
        else:
            base_arrow.data.materials.append(arrow_material)

        # Load fluid data and create instances per frame
        for frame_idx in range(total_frames):
            bpy.context.scene.frame_set(frame_idx)

            # Evaluate time-dependent visualization parameters for the current frame
            current_viz_params = {}
            for key, value in visualization_params.items():
                if isinstance(value, str):
                    try:
                        current_viz_params[key] = self.param_evaluator.evaluate(value, t=frame_idx)
                    except ValueError as e:
                        print(f"Error evaluating visualization parameter '{key}' at frame {frame_idx}: {e}", file=sys.stderr)
                        current_viz_params[key] = visualization_params.get(key) # Fallback to original
                elif isinstance(value, list):
                    evaluated_list = []
                    for item in value:
                        if isinstance(item, str):
                            try:
                                evaluated_list.append(self.param_evaluator.evaluate(item, t=frame_idx))
                            except ValueError as e:
                                print(f"Error evaluating list item in visualization parameter '{key}' at frame {frame_idx}: {e}", file=sys.stderr)
                                evaluated_list.append(item) # Fallback to original
                        else:
                            evaluated_list.append(item)
                    current_viz_params[key] = evaluated_list
                else:
                    current_viz_params[key] = value
            
            # Evaluate time-dependent simulation parameters that might affect visualization
            current_sim_params = {}
            for key, value in simulation_params.items():
                if isinstance(value, str):
                    try:
                        current_sim_params[key] = self.param_evaluator.evaluate(value, t=frame_idx)
                    except ValueError as e:
                        print(f"Error evaluating simulation parameter '{key}' at frame {frame_idx}: {e}", file=sys.stderr)
                        current_sim_params[key] = simulation_params.get(key) # Fallback to original
                else:
                    current_sim_params[key] = value

            # Update material properties
            arrow_color = current_viz_params.get("arrow_color", [0.0, 0.0, 0.8])
            emission_strength = current_viz_params.get("emission_strength", 50.0)
            transparency_alpha = current_viz_params.get("transparency_alpha", 0.1)
            light_energy = current_viz_params.get("light_energy", 3.0)
            camera_location = current_viz_params.get("camera_location", [0, -5, 2])

            arrow_material.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (*arrow_color, 1)
            arrow_material.node_tree.nodes["Emission"].inputs['Color'].default_value = (*arrow_color, 1)
            arrow_material.node_tree.nodes["Emission"].inputs['Strength'].default_value = emission_strength
            arrow_material.node_tree.nodes["Principled BSDF"].inputs['Alpha'].default_value = transparency_alpha
            
            # Update light and camera
            bpy.data.lights['Sun'].energy = light_energy
            bpy.context.scene.camera.location = camera_location

            # Load fluid data for the current frame
            frame_fluid_data_path = os.path.join(fluid_data_path, f"fluid_data_frame_{frame_idx:04d}.npz")
            if not os.path.exists(frame_fluid_data_path):
                print(f"Warning: Fluid data for frame {frame_idx} not found at {frame_fluid_data_path}", file=sys.stderr)
                continue
            fluid_data = np.load(frame_fluid_data_path)
            u = fluid_data['u']
            v = fluid_data['v']
            x = fluid_data['x']
            y = fluid_data['y']

            # Clear previous arrows for this frame (if any) - for animation
            # For instancing, we create them once and update visibility/position
            # For now, we'll just create new ones and let Blender handle cleanup if needed
            # A more efficient way would be to update existing instances.
            for obj in fluid_collection.objects:
                if obj.name.startswith("FluidArrow_"):
                    bpy.data.objects.remove(obj, do_unlink=True)

            # Create arrows based on fluid velocity (simplified)
            arrow_density = current_viz_params.get("arrow_density", 15)
            arrow_scale_factor = current_viz_params.get("arrow_scale_factor", 3.0)

            # Downsample grid for arrow visualization
            step_x = max(1, u.shape[0] // arrow_density)
            step_y = max(1, u.shape[1] // arrow_density)

            for i_x in range(0, u.shape[0], step_x):
                for i_y in range(0, u.shape[1], step_y):
                    pos_x = x[i_x]
                    pos_y = y[i_y]
                    vel_u = u[i_x, i_y]
                    vel_v = v[i_x, i_y]

                    speed = np.sqrt(vel_u**2 + vel_v**2)
                    if speed > 1e-6: # Avoid division by zero for zero velocity
                        direction_x = vel_u / speed
                        direction_y = vel_v / speed

                        # Create an instance of the base arrow
                        arrow_instance = bpy.data.objects.new(f"FluidArrow_{frame_idx}_{i_x}_{i_y}", base_arrow.data)
                        fluid_collection.objects.link(arrow_instance)
                        arrow_instance.location = (pos_x, pos_y, 0) # Z-position can be adjusted
                        
                        # Scale arrow based on speed
                        arrow_instance.scale = (arrow_scale_factor * speed, arrow_scale_factor * speed, arrow_scale_factor * speed)

                        # Rotate arrow to align with velocity direction
                        # Angle from positive X-axis to (direction_x, direction_y)
                        angle = np.arctan2(direction_y, direction_x)
                        arrow_instance.rotation_euler = (0, 0, angle)

            # Render the current frame
            bpy.context.scene.render.filepath = os.path.join(render_output_path, f"frame_{frame_idx:04d}")
            bpy.ops.render.render(write_still=True)

        print("Blender rendering complete.")


if __name__ == "__main__":
    # This script is intended to be run from Blender using --python
    # Arguments are passed after --
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
        if len(argv) == 4:
            fluid_data_path = argv[0]
            render_output_path = argv[1]
            simulation_params_json = argv[2]
            visualization_params_json = argv[3]

            visualizer = BlenderFluidVisualizer()
            visualizer.setup_scene_and_render(fluid_data_path, render_output_path, simulation_params_json, visualization_params_json)
        else:
            print("Error: Expected 4 arguments (fluid_data_path, render_output_path, simulation_params_json, visualization_params_json) after --", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Arguments must be passed after --", file=sys.stderr)
        sys.exit(1)
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
        print(f"[DEBUG] Raw devices from get_devices(): {cycles_prefs.get_devices()}") # Added for debugging
        for device in cycles_prefs.devices:
            print(f"[INFO] - Device: {device.name}, Type: {device.type}, Use: {device.use}") # Enhanced logging

        # Set compute device type (CUDA is generally well-supported)
        # Check for OPTIX first, then CUDA
        if any(d.type == 'OPTIX' for d in cycles_prefs.devices):
            cycles_prefs.compute_device_type = 'OPTIX'
        elif any(d.type == 'CUDA' for d in cycles_prefs.devices):
            cycles_prefs.compute_device_type = 'CUDA'
        else:
            cycles_prefs.compute_device_type = 'NONE' # Fallback if neither found
        print(f"[INFO] Set compute device type to {cycles_prefs.compute_device_type}.")

        # Enable GPU devices based on the chosen compute_device_type
        gpu_devices = [d for d in cycles_prefs.devices if d.type == cycles_prefs.compute_device_type]

        if not gpu_devices:
            print("[WARNING] No compatible CUDA/OPTIX GPU found inside the container.")
            print("[WARNING] Falling back to CPU rendering.")
            bpy.context.scene.cycles.device = 'CPU'
        else:
            print("[INFO] Enabling compatible GPU devices...")
            # Unselect all devices first
            for device in cycles_prefs.devices:
                device.use = False
            
            # Enable all found GPUs
            enabled_device_names = [] # New list to store names
            for device in gpu_devices:
                device.use = True
                enabled_device_names.append(device.name) # Store name
                print(f"[INFO] Enabled GPU device: {device.name}")
            
            bpy.context.scene.cycles.device = 'GPU'
            print(f"[SUCCESS] GPU rendering is configured. Enabled devices: {', '.join(enabled_device_names)}") # Enhanced log

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
    principled_node.inputs['Emission Color'].default_value = (*base_color_rgb, 1.0)
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
    principled_node.inputs['Emission Color'].default_value = (*emission_color, 1.0)
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

def animate_getsuga_vfx(all_fluid_data, mesh_objects, viz_params, scene):
    print("Animating Getsuga Tenshou VFX...")
    
    anim_params = viz_params.get("animation_params", {})
    material_params = viz_params.get("material_params", {})
    
    dissipation_start = anim_params.get("dissipation_start_frame", scene.frame_end - 30)
    dissipation_end = anim_params.get("dissipation_end_frame", scene.frame_end)
    forward_motion = np.array(anim_params.get("forward_motion", [0, 0.2, 0]))
    
    getsuga_material = bpy.data.materials.get("GetsugaMaterial")
    if not getsuga_material or not getsuga_material.use_nodes:
        print("Error: GetsugaMaterial not found or does not use nodes. Cannot animate material.")
        return
    principled_node = getsuga_material.node_tree.nodes.get('Principled BSDF')
    if not principled_node:
        print("Error: Principled BSDF node not found in GetsugaMaterial. Cannot animate material.")
        return

    # --- Animate Material Properties over the entire timeline ---
    for frame in range(scene.frame_start, scene.frame_end + 1):
        # Dissipation (투명도/밝기 점점 감소)
        if dissipation_start <= frame <= dissipation_end:
            # Calculate dissipation factor (0.0 at start, 1.0 at end)
            factor = (frame - dissipation_start) / (dissipation_end - dissipation_start)
            
            # Fade out emission strength
            current_emission_strength = material_params.get("emission_strength", 5.0) * (1 - factor)
            principled_node.inputs['Emission Strength'].default_value = current_emission_strength
            
            # Fade out alpha (become more transparent)
            current_alpha = material_params.get("transparency_alpha", 0.7) * (1 - factor)
            principled_node.inputs['Alpha'].default_value = current_alpha
        elif frame < dissipation_start:
            # Before dissipation, use full values
            principled_node.inputs['Emission Strength'].default_value = material_params.get("emission_strength", 5.0)
            principled_node.inputs['Alpha'].default_value = material_params.get("transparency_alpha", 0.7)
        else: # frame > dissipation_end
            # After dissipation, fully transparent/dark
            principled_node.inputs['Emission Strength'].default_value = 0.0
            principled_node.inputs['Alpha'].default_value = 0.0
        
        # Insert keyframes for the material properties at the current frame
        principled_node.inputs['Emission Strength'].keyframe_insert(data_path="default_value", frame=frame)
        principled_node.inputs['Alpha'].keyframe_insert(data_path="default_value", frame=frame)

    # --- Animate Object Visibility and Position ---
    for frame_idx, obj in enumerate(mesh_objects):
        if frame_idx > scene.frame_end:
            continue

        # The object's base position is determined by the forward motion
        obj.location = forward_motion * frame_idx
        obj.keyframe_insert(data_path="location", frame=frame_idx)

        # The object should only be visible on its corresponding frame
        # Hide it on the frame before it appears
        if frame_idx > scene.frame_start:
            obj.hide_set(True)
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx - 1)
            obj.keyframe_insert(data_path="hide_render", frame=frame_idx - 1)

        # Show it on its correct frame
        obj.hide_set(False)
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx)
        obj.keyframe_insert(data_path="hide_render", frame=frame_idx)

        # Hide it on the frame after it appears
        if frame_idx < scene.frame_end:
            obj.hide_set(True)
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx + 1)
            obj.keyframe_insert(data_path="hide_render", frame=frame_idx + 1)

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
        if frame_idx > scene.frame_end:
            break # Don't create more objects than frames in the scene
        print(f"[DEBUG] Processing frame {frame_idx}...")

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

        mesh_objects.append(mesh_obj)
    print(f"[INFO] Generated {len(mesh_objects)} mesh objects.")
    
    # 4. Animate meshes and material properties
    animate_getsuga_vfx(all_fluid_data, mesh_objects, viz_params, scene)

    # --- Setup Camera and Light (Basic) ---
    print("[INFO] Setting up camera and lights...")
    # Remove default cube if it exists
    if "Cube" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)

    # Add a camera
    bpy.ops.object.camera_add(location=(10, -15, 5)) # Adjusted for better view
    camera = bpy.context.object
    scene.camera = camera
    # Point camera towards the origin (where the effect starts)
    # This uses a Track To constraint for simplicity
    track_to_empty = bpy.data.objects.new("TrackTarget", None)
    scene.collection.objects.link(track_to_empty)
    track_to_empty.location = (0, 5, 0) # Look slightly ahead of the start
    constraint = camera.constraints.new(type='TRACK_TO')
    constraint.target = track_to_empty

    # Add a light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    light = bpy.context.object
    light.data.energy = 3.0
    light.data.angle = 0.5 # Softer shadows

    # Add a floor plane
    bpy.ops.mesh.primitive_plane_add(size=50, enter_editmode=False, align='WORLD', location=(0, 0, -0.1))
    floor_obj = bpy.context.object
    floor_obj.name = "Floor"
    floor_mat = create_basic_material("FloorMaterial", (0.1, 0.1, 0.1), 0.0)
    if floor_obj.data.materials:
        floor_obj.data.materials[0] = floor_mat
    else:
        floor_obj.data.materials.append(floor_mat)

    # --- Camera Animation (Simple Pan) ---
    print("[INFO] Setting up camera animation...")
    # The Track To constraint handles rotation, so we only animate the target's location
    track_to_empty.location = (0, 5, 0)
    track_to_empty.keyframe_insert(data_path="location", frame=scene.frame_start)
    
    track_to_empty.location = (0, 15, 0) # Follow the effect
    track_to_empty.keyframe_insert(data_path="location", frame=scene.frame_end)

    print("Camera animation complete.")

    # --- Save Blend File ---
    print(f"[INFO] Saving final .blend file to {output_blend_path}...")
    # Ensure render engine and device are set to CYCLES/GPU right before saving
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    try:
        bpy.ops.wm.save_as_mainfile(filepath=output_blend_path)
        print(f"Blender file saved to {output_blend_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save .blend file: {e}")
        sys.exit(1)
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