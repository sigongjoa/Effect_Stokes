# Fluid Effect Generation API Specification

This document outlines the API for generating fluid simulation effects in Blender, driven by high-level descriptions. This API is intended to be used by an LLM (Large Language Model) to translate natural language requests into concrete simulation and visualization parameters.

---

## API Function: `create_fluid_effect`

*   **Purpose:** Generates a fluid simulation effect in Blender based on a high-level natural language description and specified parameters. This function orchestrates the Navier-Stokes simulation and its Blender visualization.
*   **Conceptual Endpoint/Method:** This would be an internal function call within the `simulation_agent` or a similar orchestrator.

### Input Parameters:

1.  `effect_description`: `str` (Required)
    *   **Description:** A natural language description of the desired fluid effect. The LLM will parse this to infer simulation and visualization parameters.
    *   **Examples:**
        *   `"a crescent-shaped sword energy moving quickly to the right"`
        *   `"a slow, swirling vortex of green smoke that dissipates quickly"`
        *   `"a gentle ripple expanding from a central point"`
        *   `"a turbulent explosion of red liquid"`

2.  `simulation_params`: `dict` (Optional)
    *   **Description:** Explicit numerical parameters for the Navier-Stokes simulation. If provided, these override parameters inferred from `effect_description`.
    *   **Keys (Examples):**
        *   `grid_resolution`: `tuple[int, int]` (e.g., `(80, 80)`) - `nx`, `ny`
        *   `time_steps`: `int` (e.g., `1000`) - `nt`
        *   `viscosity`: `float` (e.g., `0.05`) - `nu`
        *   `initial_shape_type`: `str` (e.g., `"crescent"`, `"circle"`, `"vortex"`, `"custom_mask"`)
        *   `initial_shape_position`: `tuple[float, float]` (e.g., `(0.5, 1.0)`)
        *   `initial_shape_size`: `float` (e.g., `0.3`)
        *   `initial_velocity`: `tuple[float, float]` (e.g., `(0.5, 0.1)`)
        *   `force_field_type`: `str` (e.g., `"none"`, `"vortex"`, `"sink"`, `"source"`)
        *   `force_strength`: `float`
        *   `boundary_conditions`: `str` (e.g., `"no_slip_walls"`, `"open"`, `"periodic"`)
        *   `vortex_strength`: `float` (Specific to vortex type)
        *   `source_strength`: `float` (Specific to source type)

3.  `visualization_params`: `dict` (Optional)
    *   **Description:** Explicit parameters for how the fluid effect should be visualized in Blender. If provided, these override inferred parameters.
    *   **Keys (Examples):**
        *   `visualization_type`: `str` (e.g., `"arrows"`, `"particles"`, `"volume"`, `"streamlines"`)
        *   `arrow_color`: `tuple[float, float, float]` (RGB, e.g., `(0.0, 1.0, 0.0)` for green)
        *   `arrow_scale_factor`: `float` (e.g., `2.0`)
        *   `arrow_density`: `int` (e.g., `10` for 10x10 grid of arrows)
        *   `particle_count`: `int` (If `visualization_type` is "particles")
        *   `particle_size`: `float` (If `visualization_type` is "particles")
        *   `render_output_format`: `str` (e.g., `"blend"`, `"mp4"`, `"gif"`) - *Note: This implies a post-processing step that is currently not implemented but would be a natural extension.*

### Output: `dict`

*   **Description:** A dictionary containing the status of the operation and the path to the generated Blender file (or other output).
*   **Keys:**
    *   `status`: `str` (`"success"` or `"failure"`)
    *   `message`: `str` (Human-readable status or error message)
    *   `output_file_path`: `str` (Absolute path to the generated `.blend` file, or other output if `render_output_format` is specified)
    *   `inferred_simulation_params`: `dict` (The actual simulation parameters used, after inference/override)
    *   `inferred_visualization_params`: `dict` (The actual visualization parameters used, after inference/override)

### Error Handling:

*   `ValueError`: If `effect_description` is ambiguous or cannot be parsed, or if required parameters are missing/invalid.
*   `SimulationError`: If the Navier-Stokes simulation fails.
*   `BlenderVisualizationError`: If the Blender script fails to generate the visualization.
*   `Exception`: For any other unexpected errors.

---

## How an LLM would use this API:

1.  **Receive User Request:** "Create a fast, red, circular burst of fluid."
2.  **Call `create_fluid_effect`:** The LLM would translate the natural language request into an API call, potentially providing explicit `simulation_params` and `visualization_params` to ensure accuracy or specific effects.

    ```python
    create_fluid_effect(
        effect_description="a fast, red, circular burst of fluid",
        simulation_params={
            "initial_shape_type": "circle_burst",
            "initial_shape_position": (1.0, 1.0), # Center of the domain
            "initial_shape_size": 0.1,
            "initial_velocity": (0.0, 0.0), # Burst from center
            "source_strength": 0.8, # Strong source for burst
            "viscosity": 0.01, # Fast dissipation
            "time_steps": 1200
        },
        visualization_params={
            "arrow_color": (1.0, 0.0, 0.0), # Red
            "visualization_type": "arrows",
            "arrow_scale_factor": 2.5
        }
    )
    ```
    *Note: The LLM could also omit `simulation_params` and `visualization_params` and let the API infer everything from `effect_description` if the inference logic within `simulation_agent` is robust enough.*
