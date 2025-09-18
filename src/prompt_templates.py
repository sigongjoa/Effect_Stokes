PROMPT_TEMPLATES = {
    "extract_vfx_params": '''
    You are a helpful assistant that extracts structured data from user prompts.
    From the following user prompt, extract the key VFX parameters.
    The user prompt is: "{user_prompt}"

    Extract the following parameters and provide the output in a valid JSON format:
    - "vfx_type": (string) The main subject of the VFX. e.g., "fire punch", "smoke".
    - "style": (string) The artistic style. e.g., "cartoonish", "realistic", "demon slayer style".
    - "duration": (integer) The duration of the effect in seconds.
    - "colors": (list of strings) The primary colors mentioned.
    - "camera_speed": (string) The described camera motion. e.g., "slow-motion", "fast-paced".

    If a parameter is not mentioned, use a sensible default or null.
    Provide only the JSON object as your response.
    ''',
    "blender_style_script": '''
    You are an expert in Blender's Python API (bpy).
    Generate a Python script for Blender that styles a pre-existing fluid simulation.

    The script should perform the following actions:
    1.  Assume a Mantaflow fluid domain object named 'FluidDomain' already exists in the scene.
    2.  Create a new material named "FluidMaterial" for the 'FluidDomain' object.
    3.  Set the material's base color to a color that matches the primary color from {colors}.
    4.  Set the render engine to EEVEE for speed.
    5.  Set the output path for the render to "/workspace/outputs/styled_frame.png".
    6.  Render a single frame (the 50th frame of the animation).

    Provide only the Python code for Blender. Do not add explanations.
    Example of expected output:
    ```python
    import bpy
    # Your code here
    ```
    ''',
    "vision_feedback": '''
    You are an expert art director providing feedback on a VFX shot.
    The user's original request was: "{style}"
    
    Analyze the attached image.
    Based on the user's request, provide feedback in a valid JSON format:
    - "is_perfect": (boolean) true if the image perfectly matches the style, false otherwise.
    - "suggestions": (string) If not perfect, provide a brief, constructive suggestion for what to change to better match the style. For example, "Make the lines bolder and the colors more vibrant." If perfect, this can be an empty string.

    Provide only the JSON object as your response. Do not include any other text or explanations.
    ''',
    "blender_final_render_script": '''
    You are an expert in Blender's Python API (bpy).
    Generate a Python script to render a final animation based on a pre-styled scene.

    The script should perform the following actions:
    1.  Assume the scene is already set up with the correct styling.
    2.  Set the render engine to EEVEE.
    3.  Set the output file format to FFmpeg video.
    4.  Set the container to MPEG-4 and video codec to H.264.
    5.  Set the output file path to "/workspace/outputs/final_video.mp4".
    6.  Set the animation start and end frames based on a duration of {duration} seconds at 24 fps.
    7.  Render the full animation.

    Provide only the Python code for Blender. Do not add explanations.
        ''',
}