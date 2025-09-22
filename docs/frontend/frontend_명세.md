# 프론트엔드 명세 및 정의서 (Frontend Specifications & Definitions)

## 1. 백엔드 API 명세 (Backend API Specifications)

Flask 백엔드 서버는 프론트엔드와의 통신 및 파이프라인 실행 관리를 위한 RESTful API 엔드포인트를 제공합니다.

### 1.1. 파이프라인 실행 API (Run Pipeline API)

*   **엔드포인트:** `/api/run_pipeline`
*   **메서드:** `POST`
*   **설명:** 클라이언트로부터 시뮬레이션 및 시각화 파라미터를 받아 Python 파이프라인(`run_full_pipeline.py`)을 실행하고, 실행 로그를 실시간으로 스트리밍합니다.
*   **요청 (Request):**
    *   **Content-Type:** `application/json`
    *   **Body:**
        ```json
        {
            "simulation_params": {
                "grid_resolution": [101, 101],
                "time_steps": 30,
                "viscosity": 0.02,
                "initial_shape_type": "vortex",
                "initial_shape_position": [1.0, 1.0],
                "initial_shape_size": 0.4,
                "initial_velocity": [0.0, 0.0],
                "boundary_conditions": "no_slip_walls",
                "vortex_strength": 1.2,
                "source_strength": 2.0
            },
            "visualization_params": {
                "arrow_color": [0.0, 0.0, 0.8],
                "arrow_scale_factor": 3.0,
                "arrow_density": 15,
                "emission_strength": 50.0,
                "transparency_alpha": 0.1
            }
        }
        ```
        *   `simulation_params`: `src/run_full_simulation.py`에 전달될 시뮬레이션 파라미터 딕셔너리.
        *   `visualization_params`: `src/run_full_simulation.py`에 전달될 시각화 파라미터 딕셔너리.
*   **응답 (Response):**
    *   **Content-Type:** `application/json`
    *   **Body (성공 시):**
        ```json
        {
            "status": "success",
            "message": "Pipeline started successfully.",
            "process_id": "unique_process_id" // 파이프라인 프로세스 식별자 (선택 사항)
        }
        ```
    *   **Body (실패 시 - 파라미터 유효성 검사 실패 등):**
        ```json
        {
            "status": "error",
            "message": "Invalid parameters provided.",
            "details": {
                "param_name": "Error message"
            }
        }
        ```
*   **실시간 로그 스트리밍:**
    *   **기술:** Socket.IO
    *   **이벤트:** `pipeline_log`
    *   **데이터:** 파이프라인(`run_full_pipeline.py`)의 표준 출력(stdout)에서 캡처된 각 라인.
        ```json
        {
            "type": "log",
            "message": "Executing: /path/to/blender --background ..."
        }
        ```
    *   **이벤트:** `pipeline_progress` (렌더링 단계에서만)
    *   **데이터:** 렌더링 진행률 정보 (Blender 로그에서 파싱)
        ```json
        {
            "type": "progress",
            "frame": 1,
            "total_frames": 30,
            "sample": 1234,
            "total_samples": 4096,
            "percentage": 50.5 // (frame / total_frames) * 100
        }
        ```
    *   **이벤트:** `pipeline_status`
    *   **데이터:** 파이프라인의 최종 상태
        ```json
        {
            "type": "status",
            "status": "completed", // "completed", "failed", "stopped"
            "message": "Pipeline finished successfully.",
            "output_dir": "/path/to/rendered_frames" // 렌더링된 프레임이 저장된 서버 경로
        }
        ```

### 1.2. 결과 이미지 제공 API (Result Images API)

*   **엔드포인트:** `/api/results/<output_dir_name>/<filename>`
*   **메서드:** `GET`
*   **설명:** 렌더링된 이미지 파일(`frame_####.png`)을 프론트엔드에 제공합니다. 백엔드 서버는 `outputs/temp_frames/` 경로를 정적 파일로 서빙하도록 설정됩니다.
*   **요청 (Request):** 없음
*   **응답 (Response):** 이미지 파일 (`image/png`)

### 1.3. 비디오 합성 API (Video Synthesis API)

*   **엔드포인트:** `/api/synthesize_video`
*   **메서드:** `POST`
*   **설명:** 렌더링된 PNG 프레임 시퀀스를 받아 MP4 또는 WebM 비디오 파일로 합성합니다. FFmpeg 라이브러리를 백엔드에서 사용합니다.
*   **요청 (Request):**
    *   **Content-Type:** `application/json`
    *   **Body:**
        ```json
        {
            "image_sequence_path": "/path/to/rendered_frames_directory", // 렌더링된 프레임이 있는 서버 경로
            "output_video_name": "my_vfx_animation.mp4",
            "fps": 24
        }
        ```
*   **응답 (Response):**
    *   **Content-Type:** `application/json`
    *   **Body (성공 시):**
        ```json
        {
            "status": "success",
            "message": "Video synthesis started.",
            "video_url": "/api/videos/my_vfx_animation.mp4" // 합성된 비디오 파일의 URL
        }
        ```
    *   **Body (실패 시):**
        ```json
        {
            "status": "error",
            "message": "Video synthesis failed.",
            "details": "FFmpeg error message"
        }
        ```

### 1.4. 파이프라인 중단 API (Stop Pipeline API)

*   **엔드포인트:** `/api/stop_pipeline`
*   **메서드:** `POST`
*   **설명:** 현재 실행 중인 파이프라인 프로세스를 안전하게 중단합니다.
*   **요청 (Request):** 없음 (또는 `process_id`를 포함할 수 있음)
*   **응답 (Response):**
    ```json
    {
        "status": "success",
        "message": "Pipeline stop request sent."
    }
    ```

## 2. 파라미터 정의 (Parameter Definitions)

기획서의 3.1절에 명시된 파라미터들에 대한 상세 정의입니다. 백엔드에서 유효성 검사에 활용됩니다.

### 2.1. 시뮬레이션 파라미터 (Simulation Parameters)

*   `grid_resolution`: `[int, int]` - 시뮬레이션 그리드의 해상도 (예: `[101, 101]`). 각 차원 최소 20, 최대 200.
*   `time_steps`: `int` - 시뮬레이션 총 시간 단계 수 (예: `30`). 최소 10, 최대 2000.
*   `viscosity`: `float` - 유체의 점성 (예: `0.02`). 0.001 ~ 0.1.
*   `initial_shape_type`: `string` - 초기 유체 형태 (`"vortex"`, `"crescent"`, `"circle_burst"`).
*   `initial_shape_position`: `[float, float]` - 초기 형태의 중심 위치 (예: `[1.0, 1.0]`). 각 값 0.0 ~ 2.0.
*   `initial_shape_size`: `float` - 초기 형태의 크기 (예: `0.4`). 0.1 ~ 1.0.
*   `initial_velocity`: `[float, float]` - 초기 형태에 부여될 속도 (예: `[0.0, 0.0]`). 각 값 -5.0 ~ 5.0.
*   `boundary_conditions`: `string` - 경계 조건 (`"no_slip_walls"`). (현재는 고정)
*   `vortex_strength`: `float` - 와류의 강도 (예: `1.2`). 0.0 ~ 5.0.
*   `source_strength`: `float` - 유체 방출원의 강도 (예: `2.0`). 0.0 ~ 5.0.

### 2.2. 시각화 파라미터 (Visualization Parameters)

*   `arrow_color`: `[float, float, float]` - 화살표 시각화 시 색상 (RGB, 0.0~1.0). (현재는 사용되지 않음, 향후 확장 대비)
*   `arrow_scale_factor`: `float` - 화살표 크기 배율. (현재는 사용되지 않음, 향후 확장 대비)
*   `arrow_density`: `int` - 화살표 밀도. (현재는 사용되지 않음, 향후 확장 대비)
*   `emission_strength`: `float` - 재질의 발광 강도 (예: `50.0`). 0.0 ~ 100.0.
*   `transparency_alpha`: `float` - 재질의 투명도 (예: `0.1`). 0.0 (완전 투명) ~ 1.0 (완전 불투명).

## 3. 에러 코드 정의 (Error Code Definitions)

백엔드 API에서 발생할 수 있는 주요 에러 코드 및 메시지 정의.

*   `400 Bad Request`:
    *   `INVALID_PARAMETERS`: 요청 파라미터의 형식이 잘못되었거나 유효성 검사를 통과하지 못함.
    *   `MISSING_PARAMETERS`: 필수 파라미터가 누락됨.
*   `500 Internal Server Error`:
    *   `PIPELINE_EXECUTION_FAILED`: `run_full_pipeline.py` 실행 중 오류 발생.
    *   `VIDEO_SYNTHESIS_FAILED`: 비디오 합성 중 오류 발생.
    *   `SERVER_ERROR`: 기타 서버 내부 오류.

## 4. 진행 상황 모니터링 상세 (Progress Monitoring Details)

Socket.IO를 통해 프론트엔드로 전송될 `pipeline_log` 및 `pipeline_status` 이벤트의 상세 내용.

*   **`pipeline_log` 이벤트:**
    *   `type: "log"`
    *   `message: string` - `run_full_pipeline.py`의 stdout/stderr에서 캡처된 한 줄의 텍스트.
*   **`pipeline_status` 이벤트:**
    *   `type: "status"`
    *   `status: string` - `("running", "completed", "failed", "stopped")`
    *   `message: string` - 현재 상태에 대한 설명.
    *   `current_step: string` - 현재 파이프라인 단계 (예: "simulation", "blender_processing", "video_synthesis").
    *   `progress: float` - 현재 단계의 진행률 (0.0 ~ 1.0). 렌더링 단계에서만 유효하며, `Fra:X` 로그에서 파싱.
    *   `total_frames: int` - 렌더링할 총 프레임 수.
    *   `current_frame: int` - 현재 렌더링 중인 프레임 번호.
    *   `output_url: string` - (완료 시) 최종 결과물(비디오 또는 이미지 갤러리)의 URL.
    *   `error_details: string` - (실패 시) 상세 오류 메시지.

## 5. 승인 (Approval)

위 명세에 대해 검토해주시고, 승인해주시면 다음 단계인 구현을 진행하겠습니다.
