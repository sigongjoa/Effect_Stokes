import bpy
import sys
import os

output_blend_path = "/mnt/d/progress/Effect_Stokes/outputs/test_save.blend"

# Ensure output directory exists
os.makedirs(os.path.dirname(output_blend_path), exist_ok=True)

print(f"[TEST] Attempting to save empty .blend file to: {output_blend_path}")
try:
    bpy.ops.wm.save_as_mainfile(filepath=output_blend_path)
    print(f"[TEST] Successfully saved: {output_blend_path}")
except Exception as e:
    print(f"[TEST] Error saving: {e}")
    sys.exit(1)
