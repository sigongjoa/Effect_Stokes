PROMPT_TEMPLATES = {
    "blender_simulation_script": """
    다음 파라미터를 사용하여 Blender의 Mantaflow로 유체 시뮬레이션 코드를 작성해줘.
    - VFX 종류: {vfx_type}
    - 지속 시간: {duration}초
    - 색상: {colors}
    - 카메라 속도: {camera_speed}
    
    코드는 다음과 같은 역할을 해야 해:
    1. 새 Blender 파일을 생성.
    2. '불꽃펀치'와 유사한 움직임을 만드는 유체 도메인과 유입(flow) 객체 설정.
    3. Mantaflow 시뮬레이션 설정을 완료하고, 캐시 경로는 "/workspace/outputs/cache"로, 최종 .blend 파일은 "/workspace/outputs/scene_setup.blend"로 저장.
    4. 코드만 반환해줘. 설명이나 주석은 필요 없어.
    
    """,
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
    1.  Assume a Mantaflow fluid domain object named 'fluid_domain' already exists in the scene.
    2.  Create a new material for the 'fluid_domain' object.
    3.  Use nodes to create the material. The goal is to achieve a "{style}" look.
    4.  The volume material should use the 'density', 'temperature', and 'velocity' attributes from the simulation. For example, connect the 'temperature' attribute to the 'Emission Strength' and 'Emission Color' of a 'Principled Volume' shader.
    5.  Use the colors {colors} as a guide for the emission color ramp.
    6.  Set the render engine to EEVEE for speed.
    7.  Set the output path for the render to "/workspace/outputs/styled_frame.png".
    8.  Render a single frame (the 50th frame of the animation).

    Provide only the Python code for Blender. Do not add explanations.
    ''',
    "vision_feedback": '''
    You are an expert art director providing feedback on a VFX shot.
    The user's original request was: "{style}"
    
    Analyze the attached image.
    Based on the user's request, provide feedback in a valid JSON format.
    The JSON object should have two keys:
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
    '''
}