import numpy as np
import os

def run_navier_stokes_simulation_and_save_data(output_dir):
    """
    A simple 2D Navier-Stokes solver for lid-driven cavity flow.
    Saves the velocity (u, v) and pressure (p) fields as .npz files for each time step.

    Args:
        output_dir (str): Directory to save the output .npz files.
    """
    # Simulation parameters
    nx = 41  # Number of grid points in x
    ny = 41  # Number of grid points in y
    nt = 500 # Number of time steps
    nit = 50 # Number of pressure correction iterations
    dx = 2 / (nx - 1)
    dy = 2 / (ny - 1)
    x = np.linspace(0, 2, nx)
    y = np.linspace(0, 2, ny)

    rho = 1
    nu = .1
    dt = .001

    # Initial conditions
    u = np.zeros((ny, nx))
    v = np.zeros((ny, nx))
    p = np.zeros((ny, nx))
    b = np.zeros((ny, nx))

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print("--- Starting Navier-Stokes Simulation and Saving Data ---")

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

        # Save data for current time step
        if n % 10 == 0: # Save every 10 time steps
            filename = os.path.join(output_dir, f"fluid_data_{n:04d}.npz")
            np.savez(filename, u=u, v=v, p=p, x=x, y=y)
            print(f"Saved fluid data for timestep {n} to {filename}")

    print("--- Simulation Finished and Data Saved ---")

if __name__ == "__main__":
    output_data_dir = "/mnt/d/progress/Effect_Stokes/workspace/outputs/fluid_data"
    run_navier_stokes_simulation_and_save_data(output_data_dir)