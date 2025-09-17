# src/style_agent.py
from llm_interface import LLMInterface

class StyleAgent:
    def __init__(self):
        self.llm = LLMInterface()

    def apply_style(self, sim_data_path: str, params: dict):
        """
        LLM을 통해 생성된 스크립트를 사용하여 시뮬레이션 데이터에 스타일을 적용합니다.
        (현재는 실행 부분은 모의 처리)
        """
        print(f"🎨 Applying style to {sim_data_path} with params: {params}")

        # 1. LLM에게 Blender 스타일링 스크립트 생성을 요청
        print("   LLM을 호출하여 Blender 스타일링 스크립트를 생성합니다...")
        script_code = self.llm.generate_code("blender_style_script", params)
        if not script_code:
            print("   스타일링 스크립트 생성 실패.")
            raise Exception("스타일링 스크립트 생성 실패.")

        # 2. 생성된 코드를 파일로 저장 (실제 실행 시 필요)
        script_path = "generated_scripts/style_script.py"
        print(f"   생성된 스크립트: {script_path} (실제 파일은 생성되지 않음)")

        # 3. Blender 실행 부분 (현재는 주석 처리)
        print("   [!] Blender 실행을 건너뛰고, 모의 결과물을 반환합니다.")

        # 4. API 명세에 따라 모의 결과물 경로 반환
        return "assets/renders/fire_punch_styled_0.png"
