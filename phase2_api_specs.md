## Step 2.5: `render_agent.py`의 최종 렌더링 로직 구현

### Function: `RenderAgent.finalize_render`

*   **Purpose:** 피드백 루프를 통해 완성된 최종 스타일을 기반으로, 전체 애니메이션을 비디오 파일로 렌더링합니다.
*   **Input Parameters:**
    *   `self`: (RenderAgent 인스턴스)
    *   `final_params`: `dict` - 최종 확정된 VFX 파라미터 딕셔너리. 특히 `duration` 키가 중요합니다.
    *   `blend_file_path`: `str` - 최종 스타일이 적용된 `.blend` 파일의 절대 경로.
*   **Output:** `str`
    *   **Description:** 최종 렌더링된 비디오 파일의 절대 경로.
    *   **Example:** `/workspace/outputs/final_video.mp4`
*   **Error Handling:**
    *   `ValueError`: LLM이 Blender 최종 렌더링 스크립트 생성을 실패한 경우.
    *   `FileNotFoundError`: Blender 실행 파일을 찾을 수 없는 경우.
    *   `subprocess.CalledProcessError`: Blender 실행 중 오류가 발생한 경우 (Blender 스크립트 오류 포함).
    *   `Exception`: 예상치 못한 기타 오류.
*   **Dependencies:**
    *   `os`, `subprocess` (Python 표준 라이브러리)
    *   `LLMInterface` (내부 모듈: `src/llm_interface.py`)
    *   `PROMPT_TEMPLATES` (내부 모듈: `src/prompt_templates.py`, `blender_final_render_script` 템플릿 사용)