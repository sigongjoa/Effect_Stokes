import numpy as np
import os
import sys
import json

def run_navier_stokes_simulation_and_save_data(output_dir, sim_params):
    """
    A simple 2D Navier-Stokes solver, configurable via sim_params.
    Saves the velocity (u, v) and pressure (p) fields as .npz files for each time step.

    Args:
        output_dir (str): Directory to save the output .npz files.
        sim_params (dict): Dictionary of simulation parameters.
    """
    # Simulation parameters from sim_params
    nx, ny = sim_params.get("grid_resolution", (81, 81))
    nt = sim_params.get("time_steps", 1000)
    nit = sim_params.get("nit", 50)
    nu = sim_params.get("viscosity", 0.05)
    initial_shape_type = sim_params.get("initial_shape_type", "crescent")
    initial_velocity = sim_params.get("initial_velocity", (0.5, 0.1))
    initial_shape_position = sim_params.get("initial_shape_position", (0.5, 1.0))
    initial_shape_size = sim_params.get("initial_shape_size", 0.3)
    vortex_strength = sim_params.get("vortex_strength", 0.0)
    source_strength = sim_params.get("source_strength", 0.0)

    dx = 2 / (nx - 1)
    dy = 2 / (ny - 1)
    x = np.linspace(0, 2, nx)
    y = np.linspace(0, 2, ny)

    rho = 1
    dt = .001

    # Initial conditions
    u = np.zeros((ny, nx))
    v = np.zeros((ny, nx))
    p = np.zeros((ny, nx))
    b = np.zeros((ny, nx))

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(f"--- Starting Navier-Stokes Simulation for '{initial_shape_type}' effect ---")
    print(f"Simulation Parameters: {sim_params}")

    # --- Apply Initial Conditions / Forces based on initial_shape_type ---
    Y_grid, X_grid = np.meshgrid(y, x)

    if initial_shape_type == "crescent":
        center_x, center_y = initial_shape_position
        radius_outer = initial_shape_size
        radius_inner = initial_shape_size * 0.6 # Inner radius for crescent
        angle_start = np.pi / 4
        angle_end = 3 * np.pi / 4

        dist_from_center = np.sqrt((X_grid - center_x)**2 + (Y_grid - center_y)**2)
        angle_from_center = np.arctan2(Y_grid - center_y, X_grid - center_x)
        angle_from_center = (angle_from_center + 2 * np.pi) % (2 * np.pi)

        crescent_mask = (
            (dist_from_center <= radius_outer) &
            (dist_from_center >= radius_inner) &
            (angle_from_center >= angle_start) &
            (angle_from_center <= angle_end)
        )
        u[crescent_mask] = initial_velocity[0]
        v[crescent_mask] = initial_velocity[1]

    elif initial_shape_type == "vortex":
        center_x, center_y = initial_shape_position
        radius = initial_shape_size

        dist_from_center = np.sqrt((X_grid - center_x)**2 + (Y_grid - center_y)**2)
        angle_from_center = np.arctan2(Y_grid - center_y, X_grid - center_x)

        vortex_mask = (dist_from_center <= radius)

        # Tangential velocity for vortex
        u_tangential = -vortex_strength * (Y_grid - center_y) / (dist_from_center + 1e-6)
        v_tangential = vortex_strength * (X_grid - center_x) / (dist_from_center + 1e-6)

        u[vortex_mask] = u_tangential[vortex_mask]
        v[vortex_mask] = v_tangential[vortex_mask]

    elif initial_shape_type == "circle_burst":
        center_x, center_y = initial_shape_position
        radius = initial_shape_size

        dist_from_center = np.sqrt((X_grid - center_x)**2 + (Y_grid - center_y)**2)
        circle_mask = (dist_from_center <= radius)

        # Radial velocity for burst
        u_radial = initial_velocity[0] * (X_grid - center_x) / (dist_from_center + 1e-6)
        v_radial = initial_velocity[1] * (Y_grid - center_y) / (dist_from_center + 1e-6)

        u[circle_mask] = u_radial[circle_mask]
        v[circle_mask] = v_radial[circle_mask]

    # Main simulation loop
    for n in range(nt):
        # Apply source term if present (for continuous burst/explosion)
        if source_strength > 0 and initial_shape_type == "circle_burst":
            center_x, center_y = initial_shape_position
            radius = initial_shape_size * 0.5 # Smaller source area
            dist_from_center = np.sqrt((X_grid - center_x)**2 + (Y_grid - center_y)**2)
            source_mask = (dist_from_center <= radius)
            u[source_mask] += source_strength * (X_grid[source_mask] - center_x) / (dist_from_center[source_mask] + 1e-6)
            v[source_mask] += source_strength * (Y_grid[source_mask] - center_y) / (dist_from_center[source_mask] + 1e-6)

        b[1:-1, 1:-1] = rho * (1 / dt * ((u[1:-1, 2:] - u[1:-1, 0:-2]) / (2 * dx) + (v[2:, 1:-1] - v[0:-2, 1:-1]) / (2 * dy)) -
                                  ((u[1:-1, 2:] - u[1:-1, 0:-2]) / (2 * dx))**2 - 2 * ((u[2:, 1:-1] - u[0:-2, 1:-1]) / (2 * dy) *
                                                                                    (v[1:-1, 2:] - v[1:-1, 0:-2]) / (2 * dx)) - ((v[2:, 1:-1] - v[0:-2, 1:-1]) / (2 * dy))**2)

        for it in range(nit):
            pn = p.copy()
            p[1:-1, 1:-1] = (((pn[1:-1, 2:] + pn[1:-1, 0:-2]) * dy**2 + (pn[2:, 1:-1] + pn[0:-2, 1:-1]) * dx**2) /
                           (2 * (dx**2 + dy**2)) - dx**2 * dy**2 / (2 * (dx**2 + dy**2)) * b[1:-1, 1:-1])

            # Boundary conditions for pressure (no-slip walls)
            p[:, -1] = p[:, -2]
            p[0, :] = p[1, :]
            p[:, 0] = p[:, 1]
            p[-1, :] = p[-2, :]

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

        # Boundary conditions for velocity (no-slip walls)
        u[0, :] = 0; u[:, 0] = 0; u[:, -1] = 0; u[-1, :] = 0
        v[0, :] = 0; v[-1, :] = 0; v[:, 0] = 0; v[:, -1] = 0

        # Save data for current time step
        if n % 10 == 0: # Save every 10 time steps
            filename = os.path.join(output_dir, f"fluid_data_{n:04d}.npz")
            np.savez(filename, u=u, v=v, p=p, x=x, y=y)
            # print(f"Saved fluid data for timestep {n} to {filename}") # Suppress for cleaner output

    print("--- Simulation Finished and Data Saved ---")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python navier_stokes_test.py <output_directory> <sim_params_json>")
        sys.exit(1)

    output_data_dir = sys.argv[1]
    sim_params_json = sys.argv[2]
    sim_params = json.loads(sim_params_json)

    run_navier_stokes_simulation_and_save_data(output_data_dir, sim_params)