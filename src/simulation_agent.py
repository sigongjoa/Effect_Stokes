# agents/simulation_agent.py

import subprocess
import os
from llm_interface import LLMInterface

class SimulationAgent:
    def __init__(self):
        self.llm = LLMInterface()

    def run_simulation(self, params: dict):
        """
        LLM을 통해 생성된 스크립트를 Blender에서 실행합니다.
        """
        # 1. LLM에게 Blender 시뮬레이션 스크립트 생성을 요청
        print("   LLM을 호출하여 Blender 시뮬레이션 스크립트를 생성합니다...")
        script_code = self.llm.generate_code("blender_simulation_script", params)
        if not script_code:
            print("   시뮬레이션 스크립트 생성 실패.")
            raise Exception("시뮬레이션 스크립트 생성 실패.")
        
        # 2. 생성된 코드를 파일로 저장
        # 스크립트와 결과물을 저장할 디렉토리 생성
        os.makedirs("workspace/generated_scripts", exist_ok=True)
        os.makedirs("workspace/outputs", exist_ok=True)

        script_path_host = "workspace/generated_scripts/sim_script.py"
        script_path_container = "/workspace/generated_scripts/sim_script.py" # blender_runner 컨테이너 내부 경로

        with open(script_path_host, "w") as f:
            f.write(script_code)
        print(f"   생성된 스크립트: {script_path_host}")
        
        # 3. Blender 컨테이너를 통해 스크립트 실행
        print("   Blender 컨테이너를 통해 시뮬레이션 스크립트를 실행합니다...")
        # docker compose run --rm --no-deps blender_runner --background --python /workspace/generated_scripts/sim_script.py
        command = [
            "docker", "compose", "run", "--rm", "--no-deps",
            "blender_runner",
            "--background", "--python", script_path_container
        ]
        
        try:
            # app 컨테이너 내에서 호스트의 docker daemon에 접근하여 blender_runner 실행
            subprocess.run(command, check=True)
            print("Blender 시뮬레이션 스크립트 실행 완료.")
            
            # 4. 실제 결과물 경로 반환
            return {
                "blend_file": "workspace/outputs/scene_setup.blend",
                "sim_cache": "workspace/outputs/cache" # Mantaflow 캐시는 폴더로 저장됨
            }
        except subprocess.CalledProcessError as e:
            print(f"Blender 컨테이너 실행 오류: {e}")
            raise
        finally:
            # 생성된 스크립트 파일 삭제 (선택 사항)
            if os.path.exists(script_path_host):
                os.remove(script_path_host)
