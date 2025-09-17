# src/feedback_agent.py
import json
import base64
import os
from PIL import Image
from llm_interface import LLMInterface

class FeedbackAgent:
    def __init__(self):
        self.llm = LLMInterface()
        self.call_count = 0

    def _create_dummy_image(self, path: str):
        """테스트를 위한 더미 이미지 파일을 생성합니다."""
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(path)

    def analyze_render(self, render_path: str, params: dict):
        """
        LLaVA를 사용하여 렌더링된 이미지를 분석하고 피드백을 생성합니다.
        """
        print(f"🔬 Analyzing render at {render_path}")
        print("   LLM(LLaVA)을 호출하여 이미지 피드백을 생성합니다...")
        
        # TODO: 실제 렌더링된 이미지를 사용해야 함. 현재는 더미 이미지를 생성하여 테스트합니다.
        dummy_image_path = "temp_render_for_feedback.png"
        self._create_dummy_image(dummy_image_path)

        try:
            # 이미지를 읽고 base64로 인코딩
            with open(dummy_image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # LLaVA 모델에 피드백 요청
            feedback_params = {"style": params.get("style", "any")}
            feedback_json_str = self.llm.generate_vision_feedback(
                "vision_feedback",
                feedback_params,
                base64_image
            )

            # LLM 응답에서 JSON 부분만 정리
            feedback_json_str = feedback_json_str[feedback_json_str.find('{'):feedback_json_str.rfind('}')+1]
            feedback_data = json.loads(feedback_json_str)

            # self.call_count를 사용하여 루프가 무한히 돌지 않도록 강제 종료 로직 추가
            self.call_count += 1
            if self.call_count > 1:
                print("   [!] 최대 피드백 횟수 초과로 루프를 종료합니다.")
                feedback_data['is_perfect'] = True

            # updated_params가 없으면 기존 params를 사용
            if 'updated_params' not in feedback_data:
                feedback_data['updated_params'] = params

            return feedback_data

        except Exception as e:
            print(f"LLM Vision 피드백 생성 실패: {e}")
            print("피드백 생성에 실패하여 루프를 종료합니다.")
            return {"is_perfect": True, "suggestions": "Error during feedback generation.", "updated_params": params}
        finally:
            # 더미 이미지 파일 삭제
            if os.path.exists(dummy_image_path):
                os.remove(dummy_image_path)


    def apply_suggestions(self, params: dict, feedback: dict):
        """
        피드백을 기반으로 파라미터를 업데이트합니다.
        """
        print(f"💡 Applying feedback suggestions: {feedback.get('suggestions')}")
        # 실제로는 피드백을 바탕으로 파라미터를 수정해야 함
        return feedback.get("updated_params", params)
