
import bpy
import sys
import os

def verify_scene(blend_file):
    """
    Opens a .blend file and runs a series of checks to verify its integrity
    for the VFX pipeline.
    """
    try:
        bpy.ops.wm.open_mainfile(filepath=blend_file)
        print(f"--- Verification Report for: {os.path.basename(blend_file)} ---")

        # 1. Check Render Engine
        if bpy.context.scene.render.engine == 'CYCLES':
            print("[SUCCESS] Render engine is set to CYCLES.")
        else:
            raise AssertionError(f"[FAILURE] Render engine is '{bpy.context.scene.render.engine}', expected 'CYCLES'.")

        # 2. Check Render Device
        if bpy.context.scene.cycles.device == 'GPU':
            print("[SUCCESS] Cycles device is set to GPU.")
        else:
            raise AssertionError(f"[FAILURE] Cycles device is '{bpy.context.scene.cycles.device}', expected 'GPU'.")

        # 3. Check for VFX Objects
        vfx_objects = [obj for obj in bpy.data.objects if obj.name.startswith("GetsugaVFX_Frame")]
        if len(vfx_objects) > 0:
            print(f"[SUCCESS] Found {len(vfx_objects)} VFX mesh objects.")
        else:
            raise AssertionError("[FAILURE] No VFX mesh objects (named 'GetsugaVFX_Frame*') found.")

        # 4. Check if the first VFX object has geometry
        first_vfx_obj = vfx_objects[0]
        if len(first_vfx_obj.data.vertices) > 0 and len(first_vfx_obj.data.polygons) > 0:
            print(f"[SUCCESS] First VFX object ('{first_vfx_obj.name}') has {len(first_vfx_obj.data.vertices)} vertices and {len(first_vfx_obj.data.polygons)} faces.")
        else:
            raise AssertionError(f"[FAILURE] First VFX object ('{first_vfx_obj.name}') has no vertices or faces.")
        
        # 5. Check for a Camera
        if bpy.context.scene.camera:
            print(f"[SUCCESS] Scene camera '{bpy.context.scene.camera.name}' is set.")
        else:
            raise AssertionError("[FAILURE] No active camera found in the scene.")

        print("\n--- Verification PASSED ---")

    except Exception as e:
        print(f"\n--- Verification FAILED ---")
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Blender scripts are executed with arguments after '--'
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        if len(args) == 1:
            blend_file_path = args[0]
            verify_scene(blend_file_path)
        else:
            print("Usage: blender --background --python verify_blend.py -- <path_to_blend_file>")
            sys.exit(1)
    else:
        print("Error: Arguments not provided correctly.")
        sys.exit(1)
