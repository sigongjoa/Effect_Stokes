# src/render_agent.py
from llm_interface import LLMInterface

class RenderAgent:
    def __init__(self):
        self.llm = LLMInterface()

    def finalize_render(self, params: dict):
        """
        LLM을 통해 생성된 스크립트를 사용하여 최종 비디오를 렌더링합니다.
        (현재는 실행 부분은 모의 처리)
        """
        print(f"🎬 Finalizing render with params: {params}")

        # 1. LLM에게 Blender 최종 렌더링 스크립트 생성을 요청
        print("   LLM을 호출하여 Blender 최종 렌더링 스크립트를 생성합니다...")
        script_code = self.llm.generate_code("blender_final_render_script", params)
        if not script_code:
            print("   최종 렌더링 스크립트 생성 실패.")
            raise Exception("최종 렌더링 스크립트 생성 실패.")

        # 2. 생성된 코드를 파일로 저장 (실제 실행 시 필요)
        script_path = "generated_scripts/final_render_script.py"
        print(f"   생성된 스크립트: {script_path} (실제 파일은 생성되지 않음)")

        # 3. Blender 실행 부분 (현재는 주석 처리)
        print("   [!] Blender 실행을 건너뛰고, 모의 결과물을 반환합니다.")

        # 4. API 명세에 따라 모의 최종 비디오 경로 반환
        return "assets/final_renders/fire_punch_final.mp4"
