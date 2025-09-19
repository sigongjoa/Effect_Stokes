import os
import subprocess
from llm_interface import LLMInterface
from prompt_templates import PROMPT_TEMPLATES

class StyleAgent:
    def __init__(self, llm_type: str = "ollama", llm_model: str = "llama2", llm_base_url: str = "http://localhost:11434"):
        self.llm = LLMInterface(llm_type=llm_type, model_name=llm_model, base_url=llm_base_url)
        # Determine output directory based on execution environment
        # If running inside Docker, it will be /app/workspace/outputs
        # If running on host for testing, it will be ./workspace/outputs
        if os.getenv("DOCKER_CONTAINER", "false") == "true":
            self.output_dir = "/app/workspace/outputs"
        else:
            self.output_dir = os.path.join(os.getcwd(), "workspace", "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_viz_params(self, parsed_vfx_params: dict, initial_viz_params: dict = None) -> dict:
        print(f"[StyleAgent] Generating visualization parameters for: {parsed_vfx_params}")

        # LLM을 호출하여 시각화 파라미터 생성
        try:
            llm_generated_viz_params = self.llm.generate_code(
                "generate_blender_script_params",
                parsed_vfx_params
            )
            
            # 초기 파라미터가 있으면 병합 (초기 파라미터가 우선)
            final_viz_params = llm_generated_viz_params
            if initial_viz_params:
                # Deep merge for nested dictionaries
                def deep_merge(source, destination):
                    for key, value in source.items():
                        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
                            destination[key] = deep_merge(value, destination[key])
                        else:
                            destination[key] = value
                    return destination
                final_viz_params = deep_merge(initial_viz_params, llm_generated_viz_params)

            return final_viz_params
        except Exception as e:
            print(f"[StyleAgent] LLM을 통한 시각화 파라미터 생성 실패: {e}")
            print("[StyleAgent] 기본 시각화 파라미터를 사용합니다.")
            # LLM 실패 시 기본값
            return {
                "mesh_params": {"mesh_type": "ribbon", "density_factor": 0.5},
                "material_params": {"base_color": [0.0, 0.0, 0.2], "emission_color": [0.2, 0.2, 0.8], "emission_strength": 5.0, "transparency_alpha": 0.7},
                "freestyle_params": {"enable_freestyle": True, "line_thickness": 2.0, "line_color": [0.0, 0.0, 0.0]},
                "animation_params": {"dissipation_start_frame": 800, "dissipation_end_frame": 1000}
            }