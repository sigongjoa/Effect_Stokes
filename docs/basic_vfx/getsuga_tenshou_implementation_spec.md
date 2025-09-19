# Getsuga Tenshou (月牙天衝) VFX Implementation Specification

This document defines the API and functional specifications for implementing a stylized "Getsuga Tenshou"-inspired fluid visual effect within Blender, based on Navier-Stokes simulation data. This serves as a detailed blueprint for code implementation.

## 1. Overall Goal

To generate an animated Blender scene that visually represents a stylized energy wave (like Getsuga Tenshou) driven by 2D Navier-Stokes fluid simulation data. The effect should feature a distinct shape, stylized shading, and clear outlines, with a sense of movement and dissipation.

## 2. Core Components and Functions (within `blender_fluid_visualizer.py`)

The `visualize_fluid_data` function will orchestrate the following new internal functions:

### 2.1. `create_getsuga_mesh(fluid_data_frame, mesh_params)`

*   **Purpose:** Generates the mesh geometry for a single frame of the Getsuga Tenshou effect based on the fluid velocity data.
*   **Input Parameters:**
    *   `fluid_data_frame`: `dict` - Contains `u`, `v`, `x`, `y` NumPy arrays for a single simulation timestep.
    *   `mesh_params`: `dict` - Parameters controlling the mesh generation.
        *   `mesh_type`: `str` (e.g., `"ribbon"`, `"plane_slice"`, `"particle_mesh"`) - Defines the geometric primitive to use.
        *   `ribbon_width`: `float` (e.g., `0.1`) - Width of the ribbons if `mesh_type` is `"ribbon"`.
        *   `segment_length`: `float` (e.g., `0.05`) - Length of segments along streamlines for ribbon generation.
        *   `density_factor`: `float` (e.g., `0.5`) - Controls how densely streamlines are sampled for mesh generation.
        *   `min_velocity_threshold`: `float` (e.g., `0.01`) - Minimum velocity magnitude to generate mesh segments.
*   **Output:** `bpy.types.Mesh` - A Blender mesh data block. This mesh data block will then be linked to a `bpy.types.Object` in the scene.
*   **Functional Details:**
    *   Utilize the `bmesh` module for efficient procedural mesh creation.
    *   Iterate through the `fluid_data_frame` grid.
    *   For `"ribbon"` type:
        *   Sample streamlines from the `u`, `v` field. Start streamlines from points with significant velocity.
        *   Along each streamline, create a series of connected quads (ribbons) or tubes.
        *   The orientation of the ribbon should align with the flow direction.
        *   The width/thickness of the ribbon can be scaled by velocity magnitude.
    *   For `"plane_slice"` type:
        *   Create a flat plane mesh.
        *   Deform its vertices based on pressure or velocity magnitude to create a wave-like surface.
    *   The generated mesh should be positioned and scaled appropriately within the Blender scene.

### 2.2. `create_getsuga_material(material_params)`

*   **Purpose:** Creates and configures the stylized material (shader) for the Getsuga Tenshou effect.
*   **Input Parameters:**
    *   `material_params`: `dict` - Parameters controlling the material's appearance.
        *   `base_color`: `tuple[float, float, float]` (RGB, e.g., `(0.0, 0.0, 0.2)`) - Base color of the energy wave.
        *   `emission_color`: `tuple[float, float, float]` (RGB, e.g., `(0.2, 0.2, 0.8)`) - Color of the glowing edges/emission.
        *   `emission_strength`: `float` (e.g., `5.0`) - Intensity of the emission.
        *   `transparency_alpha`: `float` (e.g., `0.7`) - Overall transparency of the material.
        *   `color_ramp_stops`: `list[tuple[float, tuple[float, float, float]]]` (e.g., `[(0.0, (0.1,0.1,0.1)), (0.5, (0.0,0.0,0.2)), (1.0, (0.2,0.2,0.8))]`) - Defines the positions and colors for the toon shader's color ramp.
        *   `noise_scale`: `float` (e.g., `10.0`) - Scale of procedural noise for distortion/flicker.
        *   `noise_strength`: `float` (e.g., `0.1`) - Strength of procedural noise.
*   **Output:** `bpy.types.Material` - A Blender material configured with a node-based toon shader.
*   **Functional Details:**
    *   Create a new material and enable node-based shading.
    *   Construct a node tree using `ShaderNodeBsdfPrincipled` (for base color, emission, transparency), `ShaderNodeShaderToRGB`, `ShaderNodeTexRamp` (with `Constant` interpolation for banding), and potentially `ShaderNodeTexNoise` or `ShaderNodeTexMusgrave` for procedural effects.
    *   **Mix `ShaderNodeEmission` with `Principled BSDF`** to achieve the glowing effect.
    *   Connect nodes to achieve the desired toon shading, emission, and transparency effects.

### 2.3. `configure_freestyle(freestyle_params)`

*   **Purpose:** Configures Blender's Freestyle renderer for generating stylized outlines.
*   **Input Parameters:**
    *   `freestyle_params`: `dict` - Parameters for Freestyle configuration.
        *   `enable_freestyle`: `bool` (e.g., `True`)
        *   `line_thickness`: `float` (e.g., `2.0`) - Thickness of the outlines.
        *   `line_color`: `tuple[float, float, float]` (RGB, e.g., `(0.0, 0.0, 0.0)`) - Color of the outlines.
        *   `crease_angle`: `float` (e.g., `0.785`) - Angle threshold for detecting creases.
*   **Output:** None (modifies scene and view layer settings).
*   **Functional Details:**
    *   Enable Freestyle for the scene and view layer.
    *   Configure Freestyle Line Sets to select by edge types (e.g., crease, border) and visibility.
    *   Set line thickness and color.

### 2.4. `animate_getsuga_vfx(all_fluid_data, mesh_objects, material_params, animation_params)`

*   **Purpose:** Animates the generated meshes and their material properties over the simulation timeline.
*   **Input Parameters:**
    *   `all_fluid_data`: `list[dict]` - List of fluid data for all timesteps.
    *   `mesh_objects`: `list[bpy.types.Object]` - List of mesh objects representing the fluid effect (one per frame, or a single mesh updated per frame).
    *   `material_params`: `dict` - Parameters for material animation (e.g., transparency, emission).
    *   `animation_params`: `dict` - Parameters controlling the animation behavior.
        *   `dissipation_start_frame`: `int` (e.g., `800`) - Frame at which dissipation begins.
        *   `dissipation_end_frame`: `int` (e.g., `1000`) - Frame at which dissipation ends.
*   **Output:** None (sets keyframes on Blender objects and materials).
*   **Functional Details:**
    *   Set `scene.frame_start` and `scene.frame_end` based on `all_fluid_data` length.
    *   Iterate through each frame:
        *   **Ensure clean selection:** Before creating/manipulating objects, ensure nothing is selected (`bpy.ops.object.select_all(action='DESELECT')`) and no active object (`bpy.context.view_layer.objects.active = None`).
        *   Update mesh visibility: If `mesh_objects` contains one mesh per frame, link/unlink them. If it's a single mesh, update its geometry.
        *   Keyframe material properties: Animate `transparency_alpha` and `emission_strength` to simulate dissipation during the `dissipation_start_frame` to `dissipation_end_frame` range.
        *   Keyframe mesh transformation (location, rotation, scale) if the mesh itself is moving/changing.

## 3. Integration with `visualize_fluid_data`

The main `visualize_fluid_data` function in `blender_fluid_visualizer.py` will be updated to:

1.  Load all `fluid_data_XXXX.npz` files.
2.  Call `create_getsuga_material` to get the stylized material.
3.  Call `configure_freestyle` to set up outlines.
4.  Iterate through `all_fluid_data`:
    *   For each `fluid_data_frame`, call `create_getsuga_mesh` to generate the mesh geometry for that frame.
    *   Link the generated mesh to the scene and assign the stylized material.
    *   Store references to all generated mesh objects.
5.  Call `animate_getsuga_vfx` to animate the meshes and their material properties over the timeline.
6.  Save the final `.blend` file.

## 4. Parameters for `visualize_fluid_data` (`viz_params` update)

The `viz_params` dictionary passed to `visualize_fluid_data` will be extended to include all parameters required by the new functions:

*   `mesh_params`: `dict` (as defined in 2.1)
*   `material_params`: `dict` (as defined in 2.2)
*   `freestyle_params`: `dict` (as defined in 2.3)
*   `animation_params`: `dict` (as defined in 2.4)

This comprehensive specification provides the necessary blueprint for implementing the Getsuga Tenshou-inspired fluid VFX in Blender.