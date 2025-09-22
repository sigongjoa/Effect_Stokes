# modules/llm_interface.py

import re # Add this import

import json
import os
import ollama # Import ollama
# import openai # Remove or comment out if not using OpenAI

import sys

class LLMInterface:
    def __init__(self, llm_type="ollama", model_name="llama2", api_key=None, base_url="http://localhost:11434"):
        self.llm_type = llm_type
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

        if self.llm_type == "openai":
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        elif self.llm_type == "ollama":
            # Ollama client doesn't need an API key, but uses base_url
            self.client = ollama.Client(host=self.base_url)
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}. Choose 'openai' or 'ollama'.")

    def infer_simulation_and_visualization_parameters(self, effect_keywords):
        system_message = "You are a helpful assistant that infers simulation and visualization parameters for fluid effects."
        user_message = f"""
        Based on the following effect description, infer suitable simulation and visualization parameters.
        Effect Description: "{effect_keywords}"

        Provide the output in a single JSON object with two top-level keys: "simulation_params" and "visualization_params".

        **Important**: For parameters that can change over time, provide them as a string representing a mathematical function of 't' (time). For fixed parameters, provide them as their direct value.

        **simulation_params** should include:
        - "grid_resolution": [int, int] (e.g., [101, 101])
        - "time_steps": int (e.g., 30)
        - "viscosity": float or string (e.g., 0.02 or "0.02 + 0.01 * sin(t * 0.1)")
        - "initial_shape_type": string (e.g., "vortex", "crescent", "circle_burst")
        - "initial_shape_position": [float, float] (e.g., [1.0, 1.0])
        - "initial_shape_size": float or string (e.g., 0.4 or "0.4 + 0.1 * (t / 60)")
        - "initial_velocity": [float, float] (e.g., [0.0, 0.0])
        - "boundary_conditions": string (e.g., "no_slip_walls")
        - "vortex_strength": float or string (e.g., 1.2 or "1.2 * exp(-t / 30)") (if vfx_type is vortex)
        - "source_strength": float or string (e.g., 2.0 or "2.0 * (1 - (t / 60))") (if vfx_type is source/burst)

        **visualization_params** should include:
        - "arrow_color": [float, float, float] (RGB, e.g., [0.0, 0.0, 0.8])
        - "arrow_scale_factor": float or string (e.g., 3.0 or "3.0 + 1.0 * sin(t * 0.2)")
        - "arrow_density": int (e.g., 15)
        - "emission_strength": float or string (e.g., 50.0 or "50.0 * (t / 60)")
        - "transparency_alpha": float (e.g., 0.1)
        - "camera_location": [float, float, float] (e.g., [0, -5, 2])
        - "light_energy": float (e.g., 3.0)
        - "render_samples": int (e.g., 128)

        Ensure all values are of the correct type (float, int, string for functions, or list). Provide only the JSON object as your response.
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        print("[LLMInterface] Messages being sent to LLM for parameter inference:", file=sys.stderr)
        print(messages, file=sys.stderr)

        try:
            response = None
            if self.llm_type == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.7,
                )
                content = response.choices[0].message.content
            elif self.llm_type == "ollama":
                response = self.client.chat(
                    model=self.model_name,
                    messages=messages,
                    options={'temperature': 0.7}
                )
                print(f"DEBUG Ollama raw response for inference: {response}", file=sys.stderr)
                content = response['message']['content']
            else:
                raise ValueError("Invalid LLM type configured.")

            print(f"LLM Raw Inference Response Content: {content}", file=sys.stderr)
            match = re.search(r'{.*}', content, re.DOTALL)
            if match:
                json_content = match.group(0)
                json_content = json_content.replace("True", "true").replace("False", "false")
                parsed_json = json.loads(json_content)
                return parsed_json
            else:
                return {"error": "Could not extract valid JSON from LLM inference response.", "raw_content": content}

        except Exception as e:
            print(f"LLM Parameter Inference Error: {e}", file=sys.stderr)
            if response:
                print(f"LLM response that caused error: {response}", file=sys.stderr)
            raise

    def generate_code(self, task_name, params):
        print(f"[LLMInterface] generate_code called with task_name: {task_name}, params: {params}", file=sys.stderr)

        # 프롬프트 구성 (예시)
        if task_name == "extract_vfx_params":
            system_message = "You are a helpful assistant that extracts structured data from user prompts."
            user_message = f"""
            You are a helpful assistant that extracts structured data from user prompts.
            From the following user prompt, extract the key VFX parameters.
            The user prompt is: "{params['user_prompt']}"

            Extract the following parameters and provide the output in a valid JSON format:
            - "vfx_type": (string) The main subject of the VFX. e.g., "fire punch", "smoke".
            - "style": (string) The artistic style. e.g., "cartoonish", "realistic", "demon slayer style".
            - "duration": (integer) The duration of the effect in seconds.
            - "colors": (list of strings) The primary colors mentioned.
            - "camera_speed": (string) The described camera motion. e.g., "slow-motion", "fast-paced".

            If a parameter is not mentioned, use a sensible default or null.
            Provide only the JSON object as your response.
            """
        elif task_name == "generate_simulation_code":
            system_message = "You are a helpful assistant that generates Python code for fluid simulations."
            user_message = f"""
            Generate Python code for a 2D Navier-Stokes fluid simulation based on the following parameters:
            {json.dumps(params, indent=2)}

            The code should output fluid data (u, v, p, x, y) as NumPy arrays in a .npz file.
            Ensure the code is well-commented and follows best practices.
            Provide only the Python code block.
            """
        elif task_name == "generate_blender_script_params":
            system_message = "You are a helpful assistant that generates Blender visualization parameters."
            user_message = f"""
            Generate Blender visualization parameters (viz_params) in JSON format for a stylized VFX.
            The VFX is based on the following extracted parameters:
            {json.dumps(params, indent=2)}

            The viz_params should include:
            - "mesh_params": (dict) Parameters for mesh generation (e.g., mesh_type, density_factor).
            - "material_params": (dict) Parameters for material (e.g., base_color: [0.0, 0.0, 0.2], emission_color: [0.2, 0.2, 0.8], emission_strength, transparency_alpha).
            - "freestyle_params": (dict) Parameters for Freestyle (e.g., enable_freestyle, line_thickness, line_color).
            - "animation_params": (dict) Parameters for animation (e.g., dissipation_start_frame, dissipation_end_frame).

            Ensure the parameters are suitable for a "Getsuga Tenshou" style effect if applicable,
            and align with the provided VFX parameters.
            Provide ONLY the JSON object as your response. Do NOT include any conversational text, explanations, or markdown formatting (e.g., ```json).
            """
        else:
            raise ValueError(f"Unknown task_name: {task_name}")

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        print("[LLMInterface] Messages being sent to LLM:", file=sys.stderr)
        print(messages, file=sys.stderr)

        try:
            if self.llm_type == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_format={"type": "json_object"} if task_name in ["extract_vfx_params", "generate_blender_script_params"] else {"type": "text"},
                    temperature=0.7,
                )
                content = response.choices[0].message.content
            elif self.llm_type == "ollama":
                # Ollama's chat method
                response = self.client.chat(
                    model=self.model_name,
                    messages=messages,
                    options={'temperature': 0.7}
                )
                print(f"DEBUG Ollama raw response: {response}", file=sys.stderr)
                content = response['message']['content']
            else:
                raise ValueError("Invalid LLM type configured.")

            print(f"LLM Raw Response: {content}", file=sys.stderr)
            if task_name in ["extract_vfx_params", "generate_blender_script_params"]:
                # Use regex to find the JSON block. This is more robust.
                match = re.search(r'{.*}', content, re.DOTALL)
                if match:
                    json_content = match.group(0)
                    # Fix common JSON errors from LLMs
                    json_content = json_content.replace("True", "true").replace("False", "false")
                    parsed_json = json.loads(json_content)
                else:
                    raise ValueError("Could not extract valid JSON from LLM response.")

                # Handle nested 'viz_params' if present (from generate_blender_script_params)
                if task_name == "generate_blender_script_params" and "viz_params" in parsed_json:
                    return parsed_json["viz_params"]
                return parsed_json
            return content
        except Exception as e: # Catch all exceptions for now, refine later
            print(f"LLM 코드 생성 오류: {e}", file=sys.stderr)
            # Fallback to default or raise error
            if task_name == "extract_vfx_params":
                print("기본값으로 파이프라인을 계속 진행합니다.", file=sys.stderr)
                return {'vfx_type': 'fire', 'style': 'realistic', 'duration': 3, 'colors': ['red', 'yellow'], 'camera_speed': 'static'}
            raise
