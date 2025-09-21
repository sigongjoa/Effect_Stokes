# run_blender_oneshot.py
# This script combines scene creation, verification, and rendering into a single Blender process.

import bpy
import numpy as np
import os
import sys
import json
import bmesh

# --- Copied Functions from blender_fluid_visualizer.py ---

def enable_gpu_rendering():
    print("\n[DEBUG] --- GPU Configuration ---")
    try:
        bpy.context.scene.render.engine = 'CYCLES'
        print("[INFO] Set render engine to CYCLES.")
        cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
        cycles_prefs.compute_device_type = 'CUDA' # Or 'OPTIX'
        print(f"[INFO] Set compute device type to {cycles_prefs.compute_device_type}.")
        for device in cycles_prefs.devices:
            if device.type == cycles_prefs.compute_device_type:
                device.use = True
                print(f"[INFO] Enabled GPU device: {device.name}")
        bpy.context.scene.cycles.device = 'GPU'
        print(f"[SUCCESS] GPU rendering is configured.")
    except Exception as e:
        print(f"[ERROR] Could not enable GPU rendering: {e}. Falling back to CPU.")
        bpy.context.scene.cycles.device = 'CPU'

def create_getsuga_mesh(fluid_data_frame, mesh_params):
    # ... (This function is large, assuming it's copied verbatim)
    x_coords = fluid_data_frame['x']
    y_coords = fluid_data_frame['y']
    pressure = fluid_data_frame['p']
    nx = len(x_coords)
    ny = len(y_coords)
    pressure_threshold = mesh_params.get('pressure_threshold', 0.1)
    extrusion_scale = mesh_params.get('extrusion_scale', 0.5)
    bm = bmesh.new()
    verts = {}
    for i in range(nx):
        for j in range(ny):
            p_val = pressure[j, i]
            if p_val > pressure_threshold:
                z = p_val * extrusion_scale
                verts[(i, j)] = bm.verts.new((x_coords[i], y_coords[j], z))
            else:
                verts[(i, j)] = None
    for i in range(nx - 1):
        for j in range(ny - 1):
            v1, v2, v3, v4 = verts.get((i,j)), verts.get((i+1,j)), verts.get((i+1,j+1)), verts.get((i,j+1))
            if all([v1, v2, v3, v4]):
                try:
                    bm.faces.new((v1, v2, v3, v4))
                except ValueError:
                    pass
    mesh_data = bpy.data.meshes.new("GetsugaMesh")
    bm.to_mesh(mesh_data)
    bm.free()
    return mesh_data

def create_getsuga_material(material_params):
    # ... (Copied verbatim)
    mat = bpy.data.materials.new(name="GetsugaMaterial")
    mat.use_nodes = True
    mat.blend_method = 'BLEND' # Enable alpha blending
    nodes = mat.node_tree.nodes
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    nodes.remove(nodes.get('Material Output')) # remove default
    mat.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
    base_color = material_params.get("base_color", (0.0, 0.0, 0.2))
    emission_color = material_params.get("emission_color", (0.2, 0.2, 0.8))
    emission_strength = material_params.get("emission_strength", 5.0)
    principled_node.inputs['Base Color'].default_value = (*base_color, 1.0)
    principled_node.inputs['Emission Color'].default_value = (*emission_color, 1.0)
    principled_node.inputs['Emission Strength'].default_value = emission_strength
    return mat

def animate_getsuga_vfx(all_fluid_data, mesh_objects, viz_params, scene):
    # ... (Copied verbatim with hide_viewport fix)
    anim_params = viz_params.get("animation_params", {})
    forward_motion = np.array(anim_params.get("forward_motion", [0, 0.2, 0]))
    for frame_idx, obj in enumerate(mesh_objects):
        if frame_idx > scene.frame_end: continue
        obj.location = forward_motion * frame_idx
        obj.keyframe_insert(data_path="location", frame=frame_idx)
        if frame_idx > scene.frame_start:
            obj.hide_viewport = True
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx - 1)
            obj.keyframe_insert(data_path="hide_render", frame=frame_idx - 1)
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx)
        obj.keyframe_insert(data_path="hide_render", frame=frame_idx)
        if frame_idx < scene.frame_end:
            obj.hide_viewport = True
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx + 1)
            obj.keyframe_insert(data_path="hide_render", frame=frame_idx + 1)

# --- Main Execution Block ---

def run_oneshot_process(data_dir, render_output_path, viz_params):
    print("--- Blender One-Shot Process Started ---")
    
    # 1. Scene Setup
    print("\n--- Step 1: Setting up scene ---")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    enable_gpu_rendering() # Configure GPU rendering AFTER clearing factory settings
    scene = bpy.context.scene
    mesh_params = viz_params.get("mesh_params", {})
    material_params = viz_params.get("material_params", {})

    # 2. Load Data
    print("\n--- Step 2: Loading fluid data ---")
    fluid_data_files = sorted([f for f in os.listdir(data_dir) if f.startswith("fluid_data_") and f.endswith(".npz")])
    if not fluid_data_files:
        raise FileNotFoundError(f"No fluid data files found in {data_dir}")
    all_fluid_data = [np.load(os.path.join(data_dir, f)) for f in fluid_data_files]
    scene.frame_end = len(all_fluid_data) - 1

    # 3. Create Objects
    print("\n--- Step 3: Creating VFX objects ---")
    getsuga_material = create_getsuga_material(material_params)
    mesh_objects = []
    for i, frame_data in enumerate(all_fluid_data):
        mesh_data = create_getsuga_mesh(frame_data, mesh_params)
        mesh_obj = bpy.data.objects.new(f"GetsugaVFX_Frame_{i:04d}", mesh_data)
        scene.collection.objects.link(mesh_obj)
        mesh_obj.data.materials.append(getsuga_material)
        mesh_objects.append(mesh_obj)
    print(f"Created {len(mesh_objects)} objects.")

    # 4. Animate
    print("\n--- Step 4: Animating objects ---")
    animate_getsuga_vfx(all_fluid_data, mesh_objects, viz_params, scene)
    # Basic Camera Setup
    bpy.ops.object.camera_add(location=(10, -15, 5))
    scene.camera = bpy.context.object

    # Add a light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    light = bpy.context.object
    light.data.energy = 3.0
    light.data.angle = 0.5 # Softer shadows

    # Camera tracking setup
    track_to_empty = bpy.data.objects.new("TrackTarget", None)
    scene.collection.objects.link(track_to_empty)
    track_to_empty.location = (0, 5, 0) # Look slightly ahead of the start
    constraint = scene.camera.constraints.new(type='TRACK_TO')
    constraint.target = track_to_empty

    # 5. Internal Verification
    print("\n--- Step 5: Verifying scene before render ---")
    if scene.render.engine != 'CYCLES': raise AssertionError("Engine is not CYCLES")
    if scene.cycles.device != 'GPU': raise AssertionError("Device is not GPU")
    if not scene.camera: raise AssertionError("No camera set")
    if len(mesh_objects) == 0: raise AssertionError("No VFX objects created")
    print("Verification PASSED.")

    # 6. Render
    print("\n--- Step 6: Starting final render ---")
    scene.render.filepath = render_output_path
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(animation=True)

    print("--- Blender One-Shot Process Finished ---")

if __name__ == "__main__":
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if len(args) == 3:
            data_dir, render_path, viz_params_json = args
            viz_params = json.loads(viz_params_json)
            run_oneshot_process(data_dir, render_path, viz_params)
        else:
            print("Usage: blender --background --python run_blender_oneshot.py -- <data_dir> <render_output_path> <viz_params_json>")
            sys.exit(1)
    else:
        print("Error: No arguments provided.")
        sys.exit(1)
