# modules/llm_interface.py

import os
import openai # 또는 다른 LLM 라이브러리
from prompt_templates import PROMPT_TEMPLATES

class LLMInterface:
    def __init__(self):
        # Docker Compose에서 설정한 환경 변수를 사용하여 Ollama 서버에 연결
        self.client = openai.OpenAI(
            base_url=os.getenv("LLM_API_BASE"),
            api_key="ollama",  # Ollama는 API 키가 필요 없지만, 라이브러리 형식상 값을 제공해야 합니다.
        )

    def generate_code(self, task_name: str, params: dict):
        """
        LLM에게 특정 작업에 대한 코드를 생성하도록 요청합니다.
        
        Args:
            task_name (str): 'blender_simulation_script', 'blender_shader_script' 등
            params (dict): 코드 생성에 필요한 파라미터
            
        Returns:
            str: 생성된 Python 코드
        """
        prompt = PROMPT_TEMPLATES.get(task_name).format(**params)
        
        try:
            # TODO: 사용할 모델을 Ollama에서 설정/다운로드한 모델명으로 변경해야 합니다. (예: "llama3")
            response = self.client.chat.completions.create(
                model="llama3", 
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates Python code based on user requests."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 코드 생성 오류: {e}")
            return ""

    def generate_vision_feedback(self, task_name: str, params: dict, base64_image: str):
        """
        Vision LLM에게 이미지와 텍스트 프롬프트를 보내 피드백을 생성하도록 요청합니다.
        """
        prompt = PROMPT_TEMPLATES.get(task_name).format(**params)
        
        try:
            response = self.client.chat.completions.create(
                model="llava",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Vision 피드백 생성 오류: {e}")
            return ""

    def analyze_feedback(self, image_analysis: dict, style_guide: dict):
        """
        이미지 분석 결과와 스타일 가이드를 기반으로 피드백을 생성합니다.
        
        Args:
            image_analysis (dict): image_analyser.py가 반환한 데이터
            style_guide (dict): 사용자 프롬프트에서 추출된 스타일 가이드
            
        Returns:
            dict: 피드백 내용과 수정 제안
        """
        # TODO: LLM에게 이미지 분석 데이터와 스타일 가이드를 전달하고
        #       수정 제안을 받도록 하는 로직 구현
        # 현재는 예시 데이터 반환
        return {
            "suggestions": "라인이 더 굵고 강렬해야 해. 색감은 더 밝게.",
            "is_perfect": False
        }
