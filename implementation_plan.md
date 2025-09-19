# Effect Stokes - 단계별 구현 계획

제안해주신 개발 전략에 따라, 시스템 흐름을 먼저 검증하고 점진적으로 구체적인 기능을 구현하는 단계별 계획을 수립합니다.

## Phase 1: API 기반 구조 설계 및 흐름 검증

이 단계의 목표는 각 모듈(에이전트)이 주고받는 데이터의 형식을 명확히 정의하고, 실제 기능이 없더라도 전체 파이프라인이 정상적으로 동작하는지 테스트하는 것입니다.

### Step 1.1: API 명세 정의

각 에이전트와 시스템이 사용할 API의 입출력을 명확하게 정의합니다.

#### **Orchestrator API (Web Endpoint)**

-   **Endpoint:** `POST /vfx`
-   **Request Body:**
    ```json
    {
      "prompt": "불꽃펀치, 귀멸풍 스타일, 5초, 붉은 불꽃 + 검은 연기, 카메라 슬로모션"
    }
    ```
-   **Success Response (200 OK):**
    ```json
    {
      "message": "VFX generation complete",
      "video_path": "assets/final_renders/fire_punch_final.mp4"
    }
    ```

#### **Agent-to-Agent API (Python Internal)**

1.  **Prompt Parser (`main.py:parse_prompt`)**
    -   **Input:** `prompt: str`
    -   **Output:** `params: dict`
        ```python
        {
            "vfx_type": "불꽃펀치",
            "style": "귀멸풍",
            "duration": 5,
            "colors": ["red", "orange", "black"],
            "camera_speed": "slow-motion"
        }
        ```

2.  **Simulation Agent (`simulation_agent.run_simulation`)**
    -   **Input:** `params: dict`
    -   **Output:** `sim_output: dict`
        ```python
        {
            "sim_cache_path": "assets/simulations/fire_punch_cache",
            "blend_file_path": "assets/blender_scenes/fire_punch.blend",
            "sim_preview_path": "assets/previews/fire_punch_preview.mp4"
        }
        ```

3.  **Style Agent (`style_agent.apply_style`)**
    -   **Input:** `sim_data_path: str`, `params: dict`
    -   **Output:** `render_path: str` (e.g., `"assets/renders/fire_punch_styled_0.png"`)

4.  **Feedback Agent (`feedback_agent.analyze_render`)**
    -   **Input:** `render_path: str`, `params: dict`
    -   **Output:** `feedback: dict`
        ```python
        {
            "suggestions": "라인이 더 굵고 강렬해야 해. 색감은 더 밝게.",
            "is_perfect": False,
            "updated_params": { ... } # 수정된 파라미터
        }
        ```

5.  **Render Agent (`render_agent.finalize_render`)**
    -   **Input:** `final_render_path: str`
    -   **Output:** `final_video_path: str` (e.g., `"assets/final_renders/fire_punch_final.mp4"`)

### Step 1.2: 테스트 코드 작성 (`/tests/test_flow.py`)

API 명세에 따라, 전체 파이프라인의 흐름을 검증하는 테스트 코드를 작성합니다. 이 테스트는 각 에이전트가 모의(mock) 데이터를 반환하더라도 정상적으로 다음 단계로 넘어가는지 확인합니다.

```python
# /tests/test_flow.py
import unittest
from unittest.mock import patch
from src.main import EffectStokesOrchestrator

class TestPipelineFlow(unittest.TestCase):

    @patch('src.simulation_agent.SimulationAgent.run_simulation')
    @patch('src.style_agent.StyleAgent.apply_style')
    @patch('src.feedback_agent.FeedbackAgent.analyze_render')
    @patch('src.render_agent.RenderAgent.finalize_render')
    def test_full_pipeline_flow(self, mock_finalize, mock_analyze, mock_apply_style, mock_run_sim):
        # Mock 객체들이 API 명세에 맞는 모의 데이터를 반환하도록 설정
        mock_run_sim.return_value = "mock/sim_data"
        mock_apply_style.return_value = "mock/styled_render.png"
        # 첫 번째 피드백은 개선 제안, 두 번째는 완료를 반환
        mock_analyze.side_effect = [
            {"is_perfect": False, "suggestions": "더 강하게!", "updated_params": {}},
            {"is_perfect": True}
        ]
        mock_finalize.return_value = "mock/final_video.mp4"

        # 오케스트레이터 실행
        orchestrator = EffectStokesOrchestrator()
        final_path = orchestrator.run_pipeline("test prompt")

        # 각 에이전트가 올바르게 호출되었는지 확인
        self.assertTrue(mock_run_sim.called)
        self.assertEqual(mock_apply_style.call_count, 2) # 최초 실행 + 피드백 후 재실행
        self.assertEqual(mock_analyze.call_count, 2)
        self.assertTrue(mock_finalize.called)
        self.assertEqual(final_path, "mock/final_video.mp4")

if __name__ == '__main__':
    unittest.main()
```

### Step 1.3: 모의(Mock) 에이전트 구현

`StyleAgent`, `FeedbackAgent`, `RenderAgent` 파일을 `src` 폴더에 생성하고, API 명세에 정의된 함수와 하드코딩된 반환 값을 추가합니다.

### Step 1.4: 흐름 테스트 실행

`python -m unittest tests.test_flow` 명령으로 테스트를 실행하여 전체 파이프라인의 연결성에 문제가 없는지 최종 검증합니다.

---

## Phase 2: 기능별 상세 구현

흐름 검증이 완료되면, 각 에이전트의 실제 기능을 구현합니다.

-   **Step 2.1: `main.py`의 `parse_prompt` 기능 구현 (LLM 연동)**
    -   **목표:** 사용자가 입력한 자연어 프롬프트를 시스템이 이해할 수 있는 구체적인 파라미터(vfx_type, style, colors 등)로 변환합니다.
    -   **방법:** LLM(Ollama)을 호출하여 사용자 프롬프트에서 속성을 JSON 형식으로 추출하고, 이를 파싱하여 사용합니다.

-   **Step 2.2: `simulation_agent.py`의 시뮬레이션 실행 및 `.blend` 파일 저장**
    -   **목표:** 파라미터를 기반으로 Blender 물리 시뮬레이션 씬을 구성하고, 사용자가 직접 수정할 수 있는 `.blend` 파일과 시뮬레이션 캐시를 생성합니다.
    -   **방법:**
        1.  LLM이 생성한 Python 스크립트를 실행하여 Blender 씬을 구성합니다.
        2.  스크립트 실행 후의 상태를 `.blend` 파일 (예: `scene_setup.blend`) 로 저장합니다.
        3.  프로그래밍 방식으로 시뮬레이션 데이터를 베이크(Bake)합니다.
        4.  다음 단계에 캐시 데이터 경로와 `.blend` 파일 경로를 함께 전달합니다.

-   **Step 2.2.1: 시뮬레이션 검증용 GIF/MP4 생성**
    -   **목표:** 생성된 `.blend` 파일을 기반으로, 물리 데이터(속도, 밀도 등)의 흐름을 보여주는 저해상도 애니메이션(GIF 또는 MP4)을 생성합니다.
    -   **방법:**
        1.  `simulation_agent`가 별도의 렌더링 스크립트를 실행합니다.
        2.  이 스크립트는 씬의 셰이더를 단순한 물리 데이터 시각화(예: 밀도 -> 색상)용으로 임시 변경합니다.
        3.  저해상도로 짧은 프레임 시퀀스를 렌더링하여 GIF 또는 MP4 파일을 생성합니다.

-   **Step 2.3: `style_agent.py`의 스타일 적용 로직 구현 (LLM으로 셰이더 코드 생성 및 적용)**
    -   **목표:** 시뮬레이션 결과물에 사용자가 원한 특정 스타일(예: '귀멸풍')을 적용하고, 결과 확인을 위한 샘플 이미지를 렌더링합니다.
    -   **방법:** LLM을 통해 Blender 셰이더 스크립트를 생성하고, 이를 시뮬레이션 데이터에 적용하여 한 프레임의 이미지를 렌더링합니다.

-   **Step 2.4: `feedback_agent.py`의 이미지 분석 및 피드백 생성 로직 구현 (Vision-LLM 활용)**
    -   **목표:** `style_agent`가 만든 샘플 이미지를 보고, 초기 프롬프트의 요구사항과 얼마나 일치하는지 평가하여 개선점을 도출하거나 루프를 종료합니다.
    -   **방법:** 멀티모달(Vision) LLM을 사용하여 이미지를 분석하고, 결과가 완벽하지 않다면 스타일 재적용을 위한 수정된 파라미터를 생성합니다.

-   **Step 2.5: `render_agent.py`의 최종 렌더링 로직 구현**
    -   **목표:** 피드백 루프를 통해 완성된 최종 스타일을 기반으로, 전체 애니메이션을 비디오 파일로 렌더링합니다.
    -   **방법:** 최종 확정된 파라미터를 기반으로 Blender에서 전체 프레임을 `.mp4` 같은 비디오 포맷으로 렌더링합니다.

각 Step을 완료할 때마다 Phase 1에서 작성한 테스트 코드를 실행하여 시스템의 안정성을 지속적으로 확인합니다.
