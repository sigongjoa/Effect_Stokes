# main.py
import json
import subprocess
from llm_interface import LLMInterface
from simulation_agent import SimulationAgent
from style_agent import StyleAgent
from feedback_agent import FeedbackAgent
from render_agent import RenderAgent

class EffectStokesOrchestrator:
    def __init__(self):
        # 각 에이전트 인스턴스 초기화
        self.llm = LLMInterface()
        self.sim_agent = SimulationAgent()

    def run_pipeline(self, user_prompt: str):
        """
        사용자 프롬프트를 받아 VFX 생성 파이프라인을 실행합니다.
        """
        print(f"1. 사용자 프롬프트 분석 중: '{user_prompt}'")
        parsed_params = self.parse_prompt(user_prompt)
        print(f" -> 분석된 파라미터: {parsed_params}")

        print("2. 시뮬레이션 에이전트 실행...")
        sim_output = self.sim_agent.run_simulation(parsed_params)
        print(f" -> 시뮬레이션 결과물: {sim_output}")
        sim_cache_path = sim_output['sim_cache_path']
        blend_file_path = sim_output['blend_file_path']

        print("3. 시뮬레이션 완료.")
        return sim_output

    def parse_prompt(self, prompt: str):
        print("   LLM을 호출하여 프롬프트에서 파라미터를 추출합니다...")
        try:
            # LLM에게 파라미터 추출을 요청
            params_json_str = self.llm.generate_code(
                "extract_vfx_params",
                {"user_prompt": prompt}
            )
            
            # LLM의 응답에서 JSON 부분만 정리
            # (LLM이 설명 등을 포함할 경우를 대비)
            params_json_str = params_json_str[params_json_str.find('{'):params_json_str.rfind('}')+1]
            
            # JSON 문자열을 파이썬 딕셔너리로 변환
            params = json.loads(params_json_str)
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
    orchestrator = EffectStokesOrchestrator()
    orchestrator.run_pipeline("A slow-motion video of a powerful fire punch, in a demon-slayer anime style. The effect should last for 5 seconds, featuring vibrant red and black flames.")
