import bpy
import sys

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
        print(f"[DEBUG] Raw devices from get_devices(): {cycles_prefs.get_devices()}") # New line
        for device in cycles_prefs.devices:
            print(f"[INFO] - Device: {device.name}, Type: {device.type}, Use: {device.use}")

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

# Main execution block for the test script
if __name__ == "__main__":
    print("Running GPU detection test...")
    enable_gpu_rendering()
    print("GPU detection test complete.")
