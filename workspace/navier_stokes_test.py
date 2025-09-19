import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image
import shutil

def run_navier_stokes_simulation_to_gif(output_gif_path):
    """
    A simple 2D Navier-Stokes solver for lid-driven cavity flow.
    Saves the entire simulation process as a GIF animation.

    Args:
        output_gif_path (str): Path to save the output GIF animation.
    """
    # Simulation parameters
    nx = 41
    ny = 41
    nt = 500 # Time steps
    nit = 50 # Pressure correction iterations
    dx = 2 / (nx - 1)
    dy = 2 / (ny - 1)
    x = np.linspace(0, 2, nx)
    y = np.linspace(0, 2, ny)
    X, Y = np.meshgrid(x, y)

    rho = 1
    nu = .1
    dt = .001

    # Initial conditions
    u = np.zeros((ny, nx))
    v = np.zeros((ny, nx))
    p = np.zeros((ny, nx))
    b = np.zeros((ny, nx))

    # --- Frame generation setup ---
    frames_dir = os.path.join(os.path.dirname(output_gif_path), "frames")
    if os.path.exists(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir)
    frame_paths = []
    save_frame_interval = 10 # Save a frame every 10 time steps

    print("--- Starting Navier-Stokes Simulation for GIF ---")

    # Main simulation loop
    for n in range(nt):
        b[1:-1, 1:-1] = rho * (1 / dt * ((u[1:-1, 2:] - u[1:-1, 0:-2]) / (2 * dx) + (v[2:, 1:-1] - v[0:-2, 1:-1]) / (2 * dy)) -
                                  ((u[1:-1, 2:] - u[1:-1, 0:-2]) / (2 * dx))**2 - 2 * ((u[2:, 1:-1] - u[0:-2, 1:-1]) / (2 * dy) *
                                                                                    (v[1:-1, 2:] - v[1:-1, 0:-2]) / (2 * dx)) - ((v[2:, 1:-1] - v[0:-2, 1:-1]) / (2 * dy))**2)

        for it in range(nit):
            pn = p.copy()
            p[1:-1, 1:-1] = (((pn[1:-1, 2:] + pn[1:-1, 0:-2]) * dy**2 + (pn[2:, 1:-1] + pn[0:-2, 1:-1]) * dx**2) /
                           (2 * (dx**2 + dy**2)) - dx**2 * dy**2 / (2 * (dx**2 + dy**2)) * b[1:-1, 1:-1])

            p[:, -1] = p[:, -2]
            p[0, :] = p[1, :]
            p[:, 0] = p[:, 1]
            p[-1, :] = 0

        un = u.copy()
        vn = v.copy()

        u[1:-1, 1:-1] = (un[1:-1, 1:-1] - un[1:-1, 1:-1] * dt / dx * (un[1:-1, 1:-1] - un[1:-1, 0:-2]) -
                                     vn[1:-1, 1:-1] * dt / dy * (un[1:-1, 1:-1] - un[0:-2, 1:-1]) -
                                     dt / (2 * rho * dx) * (p[1:-1, 2:] - p[1:-1, 0:-2]) +
                                     nu * (dt / dx**2 * (un[1:-1, 2:] - 2 * un[1:-1, 1:-1] + un[1:-1, 0:-2]) +
                                           dt / dy**2 * (un[2:, 1:-1] - 2 * un[1:-1, 1:-1] + un[0:-2, 1:-1])))

        v[1:-1, 1:-1] = (vn[1:-1, 1:-1] - un[1:-1, 1:-1] * dt / dx * (vn[1:-1, 1:-1] - vn[1:-1, 0:-2]) -
                                     vn[1:-1, 1:-1] * dt / dy * (vn[1:-1, 1:-1] - vn[0:-2, 1:-1]) -
                                     dt / (2 * rho * dy) * (p[2:, 1:-1] - p[0:-2, 1:-1]) +
                                     nu * (dt / dx**2 * (vn[1:-1, 2:] - 2 * vn[1:-1, 1:-1] + vn[1:-1, 0:-2]) +
                                           dt / dy**2 * (vn[2:, 1:-1] - 2 * vn[1:-1, 1:-1] + vn[0:-2, 1:-1])))

        u[0, :] = 0; u[:, 0] = 0; u[:, -1] = 0; u[-1, :] = 1
        v[0, :] = 0; v[-1, :] = 0; v[:, 0] = 0; v[:, -1] = 0

        # --- Save frame at interval ---
        if n % save_frame_interval == 0:
            fig = plt.figure(figsize=(11, 7), dpi=80)
            plt.contourf(X, Y, p, alpha=0.5, cmap=plt.cm.viridis)
            plt.colorbar()
            plt.streamplot(X, Y, u, v, color='black')
            plt.title(f"Velocity Field at Timestep {n}")
            frame_path = os.path.join(frames_dir, f"frame_{n:04d}.png")
            plt.savefig(frame_path)
            plt.close(fig)
            frame_paths.append(frame_path)
            print(f"Saved frame {n}")

    print("--- Simulation Finished ---")

    # --- Assemble GIF ---
    print("--- Assembling GIF from frames ---")
    images = [Image.open(fp) for fp in frame_paths]
    images[0].save(output_gif_path, save_all=True, append_images=images[1:], duration=100, loop=0)

    # --- Cleanup ---
    shutil.rmtree(frames_dir)

    print(f"--- GIF animation saved to {output_gif_path} ---")

if __name__ == "__main__":
    output_dir = "/mnt/d/progress/Effect_Stokes/workspace/outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, "navier_stokes_animation.gif")
    run_navier_stokes_simulation_to_gif(output_file)