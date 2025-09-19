# Fluid Effect Generation Testing Plan

This document outlines the testing strategy for the fluid effect generation pipeline, covering unit, integration, and conceptual end-to-end tests.

## 1. Testable Components

The pipeline consists of the following key components:

*   **`navier_stokes_test.py`**: The core Navier-Stokes simulation solver, responsible for generating fluid dynamics data (`.npz` files).
*   **`simulation_agent.py`**: The orchestration layer, responsible for interpreting high-level effect descriptions, inferring/applying parameters, and calling the Navier-Stokes solver.
*   **`blender_fluid_visualizer.py`**: (Currently user's responsibility for artistic control, but testing principles apply) This component would be responsible for taking the fluid data and generating the Blender scene with visual effects.

## 2. Types of Tests

### 2.1. Unit Tests

Focus on individual functions or modules in isolation.

*   **For `navier_stokes_test.py` (Navier-Stokes Solver):**
    *   **Initial Conditions:**
        *   Verify that different `initial_shape_type` values (e.g., `"crescent"`, `"vortex"`, `"circle_burst"`) correctly initialize the `u` and `v` velocity fields according to their geometric definitions.
        *   Test edge cases for shape parameters (e.g., very small/large sizes, positions near boundaries).
    *   **Parameter Application:**
        *   Assert that simulation parameters like `grid_resolution`, `time_steps`, `viscosity`, `vortex_strength`, `source_strength` are correctly read and influence the simulation's numerical behavior (e.g., higher viscosity leads to faster decay of velocity).
    *   **Basic Physical Properties (Assertions):**
        *   After a short simulation run, assert basic properties like the absence of `NaN` values in `u`, `v`, `p` fields.
        *   For incompressible flow, verify that the divergence of the velocity field remains close to zero (a measure of mass conservation).
    *   **Output Format:**
        *   Confirm that `.npz` files are generated as expected.
        *   Verify that each `.npz` file contains the correct NumPy arrays (`u`, `v`, `p`, `x`, `y`) with the expected shapes and data types.

*   **For `simulation_agent.py` (Orchestration/Parameter Inference):**
    *   **Keyword Mapping:**
        *   Test various `effect_description` strings (e.g., `"a red fast vortex"`, `"slow green burst"`) to ensure they correctly map to the expected `inferred_sim_params` and `inferred_viz_params` based on the keyword inference logic.
    *   **Parameter Overrides:**
        *   Verify that explicit `simulation_params` and `visualization_params` provided in the API call correctly override the values inferred from `effect_description`.
    *   **Error Handling (Conceptual):**
        *   (If implemented) Test how the agent handles ambiguous or unparsable `effect_description` strings.

### 2.2. Integration Tests

Verify the interaction between different components.

*   **`simulation_agent.py` to `navier_stokes_test.py`:**
    *   Execute `simulation_agent.run_simulation` with various `effect_description` and `simulation_params`.
    *   Verify that `navier_stokes_test.py` is correctly invoked as a subprocess.
    *   Check for the successful creation of the `fluid_data` directory and the presence of valid `.npz` files within it.
    *   Inspect the content of a few `.npz` files to ensure they reflect the parameters passed (e.g., correct grid size, number of timesteps).

### 2.3. End-to-End Tests (Conceptual - if Blender visualization were automated)

These tests would verify the entire pipeline from input to final visual output.

*   **For `blender_fluid_visualizer.py` (if automated):**
    *   **Blender Scene Generation:**
        *   Run the script in a headless Blender instance (e.g., via Docker).
        *   Verify that a `.blend` file is successfully created at the specified output path.
    *   **Object Creation and Animation:**
        *   Programmatically inspect the generated `.blend` file (e.g., using Blender's Python API to load it in another test script).
        *   Verify the existence of expected Blender objects (e.g., fluid meshes, camera, lights).
        *   Check that keyframes are correctly set for animation (e.g., mesh transformations, material properties).
    *   **Material Application:**
        *   Confirm that the correct stylized materials (e.g., toon shader) are applied to the fluid meshes.
        *   Verify material properties (e.g., base color, emission, transparency) match the `visualization_params`.
    *   **Freestyle Configuration:**
        *   Check that Freestyle rendering is enabled and configured as expected (e.g., line thickness, color).
    *   **Visual Verification (Advanced/Manual):**
        *   Render a few frames from the generated `.blend` file.
        *   Manually inspect these rendered images to confirm the visual effect matches the expectation.
        *   (Highly advanced) Implement automated visual regression testing by comparing rendered frames against a set of reference images.

## 3. Tools

*   **Python `unittest` or `pytest`**: Standard Python testing frameworks for unit and integration tests.
*   **`subprocess` module**: For invoking `navier_stokes_test.py` and Blender (via Docker) as subprocesses within tests.
*   **`numpy`**: For asserting properties of numerical data in `.npz` files.
*   **Blender's Python API (`bpy`, `bmesh`)**: For programmatic inspection and manipulation of `.blend` files in end-to-end tests (if automated).

## 4. Test Location

*   A dedicated `tests/` directory at the project root, with subdirectories mirroring the component structure (e.g., `tests/simulation_agent/`, `tests/navier_stokes/`, `tests/blender_viz/`).

---
