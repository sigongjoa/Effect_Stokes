import numpy as np
import os
import json
from param_evaluator import ParamEvaluator

class FluidSimulator:
    def __init__(self):
        self.param_evaluator = ParamEvaluator()

    def _solve_navier_stokes(self, u, v, p, dt, dx, dy, viscosity, density, source_x, source_y, boundary_conditions):
        # This is a placeholder for the actual Navier-Stokes solver logic.
        # In a real implementation, this would involve complex numerical methods.
        # For now, we'll simulate some basic fluid behavior.

        # Apply viscosity (simplified diffusion)
        u_new = u + viscosity * dt * (np.roll(u, 1, axis=0) + np.roll(u, -1, axis=0) + np.roll(u, 1, axis=1) + np.roll(u, -1, axis=1) - 4 * u) / (dx*dx)
        v_new = v + viscosity * dt * (np.roll(v, 1, axis=0) + np.roll(v, -1, axis=0) + np.roll(v, 1, axis=1) + np.roll(v, -1, axis=1) - 4 * v) / (dy*dy)

        # Apply pressure gradient (simplified)
        u_new -= dt * (np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)) / (2 * dx * density)
        v_new -= dt * (np.roll(p, -1, axis=1) - np.roll(p, 1, axis=1)) / (2 * dy * density)

        # Add source terms (simplified)
        u_new += dt * source_x
        v_new += dt * source_y

        # Apply boundary conditions (simplified: no-slip walls)
        u_new[0, :] = 0; u_new[-1, :] = 0; u_new[:, 0] = 0; u_new[:, -1] = 0
        v_new[0, :] = 0; v_new[-1, :] = 0; v_new[:, 0] = 0; v_new[:, -1] = 0

        # Update pressure (simplified: solve for divergence-free velocity)
        divergence = (np.roll(u_new, -1, axis=0) - np.roll(u_new, 1, axis=0)) / (2 * dx) + \
                     (np.roll(v_new, -1, axis=1) - np.roll(v_new, 1, axis=1)) / (2 * dy)
        p_new = p - dt * divergence * density # Very simplified pressure update

        return u_new, v_new, p_new

    def run_simulation(self, simulation_params: dict, output_dir: str):
        # Extract and evaluate fixed parameters
        grid_resolution = simulation_params.get("grid_resolution", [101, 101])
        time_steps = simulation_params.get("time_steps", 30)
        initial_shape_type = simulation_params.get("initial_shape_type", "vortex")
        boundary_conditions = simulation_params.get("boundary_conditions", "no_slip_walls")

        nx, ny = grid_resolution
        dx = 2.0 / (nx - 1)  # Assuming a 2x2 domain
        dy = 2.0 / (ny - 1)
        dt = 0.01 # Fixed time step for solver stability
        density = 1.0 # Assume constant density

        # Initialize fluid fields
        u = np.zeros((nx, ny))
        v = np.zeros((nx, ny))
        p = np.zeros((nx, ny))

        # Create meshgrids for initial conditions
        x = np.linspace(0, 2, nx)
        y = np.linspace(0, 2, ny)
        X, Y = np.meshgrid(x, y)

        # Store evaluated parameters for each frame
        evaluated_params_per_frame = []

        for i in range(time_steps):
            t = i * dt # Current simulation time

            # Evaluate time-dependent parameters for the current time step
            current_sim_params = {}
            for key, value in simulation_params.items():
                if isinstance(value, str):
                    try:
                        current_sim_params[key] = self.param_evaluator.evaluate(value, t=t)
                    except ValueError as e:
                        raise ValueError(f"Error evaluating simulation parameter '{key}' at time {t}: {e}")
                elif isinstance(value, list):
                    evaluated_list = []
                    for item in value:
                        if isinstance(item, str):
                            try:
                                evaluated_list.append(self.param_evaluator.evaluate(item, t=t))
                            except ValueError as e:
                                raise ValueError(f"Error evaluating list item in simulation parameter '{key}' at time {t}: {e}")
                        else:
                            evaluated_list.append(item)
                    current_sim_params[key] = evaluated_list
                else:
                    current_sim_params[key] = value
            
            # Apply initial shape / source based on evaluated parameters
            source_x = np.zeros((nx, ny))
            source_y = np.zeros((nx, ny))

            initial_shape_position = current_sim_params.get("initial_shape_position", [1.0, 1.0])
            initial_shape_size = current_sim_params.get("initial_shape_size", 0.4)
            vortex_strength = current_sim_params.get("vortex_strength", 1.2)
            source_strength = current_sim_params.get("source_strength", 2.0)
            initial_velocity = current_sim_params.get("initial_velocity", [0.0, 0.0])

            # Simple initial condition application (can be expanded)
            if initial_shape_type == "vortex":
                center_x, center_y = initial_shape_position
                radius = initial_shape_size
                dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
                # Apply a vortex force
                source_x += vortex_strength * (Y - center_y) * np.exp(-(dist/radius)**2)
                source_y -= vortex_strength * (X - center_x) * np.exp(-(dist/radius)**2)
            elif initial_shape_type == "circle_burst":
                center_x, center_y = initial_shape_position
                radius = initial_shape_size
                dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
                # Apply an outward burst force
                source_x += source_strength * (X - center_x) * np.exp(-(dist/radius)**2)
                source_y += source_strength * (Y - center_y) * np.exp(-(dist/radius)**2)
            
            # Add initial velocity if any
            u += initial_velocity[0]
            v += initial_velocity[1]

            # Solve Navier-Stokes for one time step
            u, v, p = self._solve_navier_stokes(
                u, v, p, dt, dx, dy,
                current_sim_params.get("viscosity", 0.02),
                density, source_x, source_y, boundary_conditions
            )

            # Save fluid data for the current frame
            frame_output_path = os.path.join(output_dir, f"fluid_data_frame_{i:04d}.npz")
            np.savez_compressed(frame_output_path, u=u, v=v, p=p, x=x, y=y)
            
            # Store evaluated parameters for this frame (for potential later use/debugging)
            evaluated_params_per_frame.append(current_sim_params)

        return {
            "status": "success",
            "message": "Fluid data generated successfully.",
            "output_data_path": output_dir,
            "simulation_params": simulation_params, # Original (potentially function-based) params
            "evaluated_params_per_frame": evaluated_params_per_frame # All evaluated params
        }

# Example Usage (for testing the FluidSimulator directly)
if __name__ == "__main__":
    simulator = FluidSimulator()

    # Example 1: Fixed parameters
    fixed_sim_params = {
        "grid_resolution": [64, 64],
        "time_steps": 10,
        "viscosity": 0.01,
        "initial_shape_type": "vortex",
        "initial_shape_position": [1.0, 1.0],
        "initial_shape_size": 0.3,
        "vortex_strength": 1.0,
    }
    output_fixed = os.path.join(os.getcwd(), "outputs", "fluid_data_fixed")
    os.makedirs(output_fixed, exist_ok=True)
    print("Running fixed parameter simulation...")
    result_fixed = simulator.run_simulation(fixed_sim_params, output_fixed)
    print(json.dumps(result_fixed, indent=2))

    # Example 2: Time-dependent parameters
    dynamic_sim_params = {
        "grid_resolution": [64, 64],
        "time_steps": 20,
        "viscosity": "0.01 + 0.005 * sin(t * 0.5)",
        "initial_shape_type": "vortex",
        "initial_shape_position": [1.0, 1.0],
        "initial_shape_size": "0.2 + 0.1 * (t / 20)",
        "vortex_strength": "1.5 * exp(-t / 10)",
    }
    output_dynamic = os.path.join(os.getcwd(), "outputs", "fluid_data_dynamic")
    os.makedirs(output_dynamic, exist_ok=True)
    print("\nRunning dynamic parameter simulation...")
    result_dynamic = simulator.run_simulation(dynamic_sim_params, output_dynamic)
    print(json.dumps(result_dynamic, indent=2))
