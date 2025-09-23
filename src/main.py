# main.py
import json
import subprocess
from src.llm_interface import LLMInterface
from src.simulation_agent import SimulationAgent
from src.style_agent import StyleAgent
from src.feedback_agent import FeedbackAgent
from src.render_agent import RenderAgent

class EffectStokesOrchestrator:
    def __init__(self, llm_type: str = "ollama", llm_model: str = "llama2", llm_base_url: str = "http://localhost:11434"):
        # 각 에이전트 인스턴스 초기화
        self.llm = LLMInterface(llm_type=llm_type, model_name=llm_model, base_url=llm_base_url)
        self.sim_agent = SimulationAgent()
        self.style_agent = StyleAgent(llm_type=llm_type, llm_model=llm_model, llm_base_url=llm_base_url)
        self.render_agent = RenderAgent()
        # self.feedback_agent = FeedbackAgent() # 피드백 에이전트는 나중에 통합

    def run_pipeline(self, user_prompt: str, fluid_data_dir: str, output_blend_file: str, initial_viz_params: dict = None):
        """
        사용자 프롬프트를 받아 VFX 생성 파이프라인을 실행합니다.
        """
        print(f"1. 사용자 프롬프트 분석 중: '{user_prompt}'")
        parsed_params = self.parse_prompt(user_prompt)
        print(f" -> 분석된 파라미터: {parsed_params}")

        print("2. 시뮬레이션 에이전트 실행...")
        sim_output = self.sim_agent.run_simulation(parsed_params)
        print(f" -> 시뮬레이션 결과물: {sim_output}")
        fluid_data_path = sim_output['output_data_path']

        print("3. 스타일 에이전트 실행 (시각화 파라미터 생성/정제)...")
        final_viz_params = self.style_agent.generate_viz_params(parsed_params, initial_viz_params)
        print(f" -> 최종 시각화 파라미터: {final_viz_params}")

        print("4. 렌더 에이전트 실행 (Blender 시각화)...")
        render_output = self.render_agent.render_vfx(fluid_data_path, output_blend_file, final_viz_params)
        print(f" -> 렌더링 결과물: {render_output}")
        
        print("5. 파이프라인 완료.")
        return render_output

    def parse_prompt(self, prompt: str):
        print("   LLM을 호출하여 프롬프트에서 파라미터를 추출합니다...")
        try:
            # LLM에게 파라미터 추출을 요청
            params_json_str = self.llm.generate_code(
                "extract_vfx_params",
                {"user_prompt": prompt}
            )
            
            params = params_json_str # LLMInterface now returns a dict directly
            return params
        except Exception as e:
            print(f"LLM 파라미터 추출 실패: {e}")
            print("기본값으로 파이프라인을 계속 진행합니다.")
            return {
                "vfx_type": "fire",
                "style": "realistic",
                "duration": 3,
                "colors": ["red", "yellow"],
                "camera_speed": "static"
            }

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Effect Stokes VFX Generation Pipeline")
    parser.add_argument("--prompt", type=str, required=True, help="User prompt for VFX generation.")
    parser.add_argument("--fluid_data_dir", type=str, help="Directory to store fluid simulation data.")
    parser.add_argument("--output_blend_file", type=str, help="Path for the output Blender file.")
    parser.add_argument("--viz_params", type=str, help="JSON string of visualization parameters.")
    parser.add_argument("--llm_type", type=str, default="ollama", help="Type of LLM to use (openai or ollama).")
    parser.add_argument("--llm_model", type=str, default="llama2", help="Name of the LLM model to use.")
    parser.add_argument("--llm_base_url", type=str, default="http://localhost:11434", help="Base URL for the LLM API.")

    args = parser.parse_args()

    # Initialize orchestrator with LLM configuration
    orchestrator = EffectStokesOrchestrator(
        llm_type=args.llm_type,
        llm_model=args.llm_model,
        llm_base_url=args.llm_base_url
    )

    # Parse viz_params if provided
    initial_viz_params = json.loads(args.viz_params) if args.viz_params else {}

    orchestrator.run_pipeline(
        user_prompt=args.prompt,
        fluid_data_dir=args.fluid_data_dir,
        output_blend_file=args.output_blend_file,
        initial_viz_params=initial_viz_params
    )
