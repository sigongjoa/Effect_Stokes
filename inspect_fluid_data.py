
import numpy as np
import sys
import os

def inspect_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    try:
        data = np.load(file_path)
        print(f"--- Inspection Report for: {os.path.basename(file_path)} ---")
        
        for key in ['p', 'u', 'v']:
            if key in data:
                array = data[key]
                print(f"\nArray: '{key}'")
                print(f"  - Shape: {array.shape}")
                print(f"  - Min:   {np.min(array):.6f}")
                print(f"  - Max:   {np.max(array):.6f}")
                print(f"  - Mean:  {np.mean(array):.6f}")

                if key == 'p':
                    threshold = 0.1
                    above_threshold_count = np.sum(array > threshold)
                    total_points = array.size
                    percentage = (above_threshold_count / total_points) * 100
                    print(f"  - Points > {threshold}: {above_threshold_count} / {total_points} ({percentage:.2f}%)")
            else:
                print(f"\nArray: '{key}' not found in file.")

    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python inspect_fluid_data.py <path_to_npz_file>")
        sys.exit(1)
    
    inspect_file(sys.argv[1])
