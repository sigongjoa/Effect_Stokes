import sys
import subprocess

print("Installing numpy into Blender's Python environment...")
try:
    # Use Blender's bundled Python to install numpy
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
    print("numpy installed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error installing numpy: {e}")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)
