# 인터랙티브 이펙트 디자인 페이즈 API 명세서

본 문서는 '인터랙티브 이펙트 디자인 페이즈'의 구현을 위한 백엔드 API 엔드포인트들을 정의하고 명세합니다. 이 API들은 LLM 기반 파라미터 제안, 브라우저 기반 실시간 미리보기, 그리고 최종 고품질 시뮬레이션 실행을 지원합니다.

## 1. 공통 데이터 구조: 함수 기반 파라미터 정의

이 페이즈에서는 파라미터들이 고정된 값이 아닌, 시간(`t`)에 따라 변화하는 함수 형태로 정의됩니다. 이는 JSON 객체 내에 문자열 형태의 수식 또는 키프레임 배열로 표현될 수 있습니다. 백엔드는 이 정의를 해석하여 시뮬레이션에 적용합니다.

### 예시: `simulation_params` 및 `visualization_params` 구조
```json
{
  "simulation_params": {
    "grid_resolution": [101, 101], // 고정 값은 기존과 동일
    "time_steps": 60,
    "viscosity": "0.02 + 0.01 * sin(t * 0.1)", // 시간 t에 따른 변화 수식
    "initial_shape_type": "vortex",
    "initial_shape_position": [1.0, 1.0],
    "initial_shape_size": "0.4 + 0.1 * (t / 60)", // 시간 t에 따른 선형 변화 수식
    "vortex_strength": "1.2 * exp(-t / 30)", // 시간 t에 따른 감쇠 수식
    "boundary_conditions": "no_slip_walls",
    "source_strength": "2.0 * (1 - (t / 60))" // 시간 t에 따른 감소 수식
  },
  "visualization_params": {
    "arrow_color": [0.0, 0.0, 0.8],
    "arrow_scale_factor": "3.0 + 1.0 * sin(t * 0.2)",
    "arrow_density": 15,
    "emission_strength": "50.0 * (t / 60)", // 시간 t에 따른 증가 수식
    "transparency_alpha": 0.1,
    "camera_location": [0, -5, 2],
    "light_energy": 3.0,
    "render_samples": 128
  }
}
```

## 2. API 엔드포인트 명세

### 2.1. `POST /api/get_llm_inferred_params`
*   **목적**: 사용자의 자연어 이펙트 설명을 기반으로 LLM이 추론한 함수 기반 파라미터 정의를 반환합니다.
*   **메서드**: `POST`
*   **요청 본문**: `application/json`
    ```json
    {
      "effect_description": "시간에 따라 세기가 줄어드는 푸른 소용돌이"
    }
    ```
*   **응답 본문**: `application/json`
    *   `status`: `"success"` 또는 `"error"`
    *   `message`: 응답 메시지
    *   `simulation_params`: LLM이 추론한 시뮬레이션 파라미터 정의 (위의 예시 구조 참조)
    *   `visualization_params`: LLM이 추론한 시각화 파라미터 정의 (위의 예시 구조 참조)
    ```json
    {
      "status": "success",
      "message": "Parameters inferred successfully.",
      "simulation_params": { /* ... 함수 기반 파라미터 정의 ... */ },
      "visualization_params": { /* ... 함수 기반 파라미터 정의 ... */ }
    }
    ```

### 2.2. `POST /api/run_preview`
*   **목적**: 제공된 함수 기반 파라미터 정의를 사용하여 브라우저에서 실시간 미리보기를 위한 데이터를 생성하고 반환합니다. 이 엔드포인트는 프론트엔드의 WebGL/Three.js 렌더러가 이펙트를 빠르게 시각화할 수 있는 경량화된 데이터를 제공합니다.
*   **메서드**: `POST`
*   **요청 본문**: `application/json`
    *   `simulation_params`: 사용자가 수정했거나 LLM이 제안한 시뮬레이션 파라미터 정의 (위의 예시 구조 참조)
    *   `visualization_params`: 사용자가 수정했거나 LLM이 제안한 시각화 파라미터 정의 (위의 예시 구조 참조)
    *   `preview_settings`: 미리보기에 필요한 추가 설정
        *   `duration_frames`: 미리보기 프레임 수 (예: 30)
        *   `resolution_scale`: 미리보기 해상도 스케일 (예: 0.5)
    ```json
    {
      "simulation_params": { /* ... 함수 기반 파라미터 정의 ... */ },
      "visualization_params": { /* ... 함수 기반 파라미터 정의 ... */ },
      "preview_settings": {
        "duration_frames": 30,
        "resolution_scale": 0.5
      }
    }
    ```
*   **응답 본문**: `application/json`
    *   `status`: `"success"` 또는 `"error"`
    *   `message`: 응답 메시지
    *   `preview_data`: 프론트엔드 WebGL 렌더러가 이펙트를 시각화하는 데 필요한 데이터 구조. 이는 각 프레임에 대한 파라미터 값 배열, 또는 WebGL 셰이더에 직접 전달될 수 있는 형태의 데이터일 수 있습니다. (구체적인 형식은 프론트엔드 렌더러 구현에 따라 정의)
        ```json
        {
          "frame_data": [
            { "frame": 0, "vortex_strength": 1.2, "initial_shape_size": 0.4, "arrow_color": [0.0, 0.0, 0.8], /* ... 기타 파라미터 값 ... */ },
            { "frame": 1, "vortex_strength": 1.18, "initial_shape_size": 0.405, "arrow_color": [0.0, 0.0, 0.8], /* ... */ },
            // ... (duration_frames 만큼 반복)
          ]
        }
        ```
    *   **오류 응답 예시**:
        ```json
        {
          "status": "error",
          "message": "Function parsing failed for 'viscosity': Invalid mathematical expression.",
          "details": "Error at 'sin(t * 0.1))' - missing parenthesis."
        }
        ```

### 2.3. `POST /api/run_pipeline`
*   **목적**: 사용자가 확정한 함수 기반 파라미터 정의를 사용하여 전체 나비에-스트로크 시뮬레이션 및 고품질 렌더링을 실행합니다. 이 엔드포인트는 비동기적으로 파이프라인을 시작하고, 진행 상황은 SocketIO를 통해 클라이언트에 전달됩니다.
*   **메서드**: `POST`
*   **요청 본문**: `application/json`
    *   `simulation_params`: 사용자가 확정한 시뮬레이션 파라미터 정의 (위의 예시 구조 참조)
    *   `visualization_params`: 사용자가 확정한 시각화 파라미터 정의 (위의 예시 구조 참조)
    ```json
    {
      "simulation_params": { /* ... 함수 기반 파라미터 정의 ... */ },
      "visualization_params": { /* ... 함수 기반 파라미터 정의 ... */ }
    }
    ```
*   **응답 본문**: `application/json` (파이프라인 시작 확인)
    *   `status`: `"success"` 또는 `"error"`
    *   `message`: 파이프라인 시작 확인 메시지
    ```json
    {
      "status": "success",
      "message": "Pipeline execution initiated."
    }
    ```
*   **SocketIO 이벤트**: 파이프라인 진행 상황 및 최종 결과는 `pipeline_status` 및 `pipeline_log` 이벤트를 통해 실시간으로 전달됩니다.
    *   `pipeline_status`: 파이프라인의 현재 상태 (예: `running`, `completed`, `failed`, `stopped`), 진행률, 현재 단계, 최종 출력 URL 등.
    *   `pipeline_log`: 파이프라인 실행 중 발생하는 로그 메시지.

## 3. 백엔드 구현 고려사항
*   **안전한 함수 파서/인터프리터**: 백엔드는 JSON/DSL 형태로 전달된 함수 정의 문자열을 **화이트리스트 기반의 안전한 수학 표현 파서**를 사용하여 파싱하고, 시뮬레이션 루프 내에서 각 시간 단계에 해당하는 파라미터 값을 계산할 수 있는 로직을 구현해야 합니다. `eval()`과 같은 위험한 함수 사용은 엄격히 금지됩니다.
*   **파라미터 변환**: 함수 기반 파라미터 정의를 `navier_stokes_test.py` 및 Blender 스크립트가 이해할 수 있는 형태로 변환하는 계층이 필요합니다.
*   **오류 처리**: 함수 정의 파싱 오류, 유효하지 않은 파라미터 값, `t` 범위 오류, 시뮬레이션/렌더링 오류 등에 대한 견고한 오류 처리 메커니즘이 필요합니다.

## 4. 프론트엔드 연동 가이드

### 4.1. WebSocket 이벤트 처리 예시
프론트엔드는 SocketIO 클라이언트를 통해 백엔드로부터 `pipeline_status` 및 `pipeline_log` 이벤트를 수신하여 UI를 업데이트합니다.

*   **`pipeline_status` 이벤트**: 파이프라인의 전반적인 상태 변화를 알립니다.
    ```javascript
    socket.on('pipeline_status', (data) => {
      console.log('Pipeline Status:', data);
      // 예시: 진행률 바 업데이트
      if (data.progress !== undefined) {
        document.getElementById('progressBar').style.width = data.progress + '%';
        document.getElementById('progressText').innerText = `진행률: ${data.progress.toFixed(2)}%`;
      }
      // 예시: 현재 단계 표시
      if (data.current_step) {
        document.getElementById('currentStep').innerText = `현재 단계: ${data.current_step}`;
      }
      // 예시: 최종 결과 URL 표시
      if (data.status === 'completed' && data.gif_url) {
        document.getElementById('resultGif').src = data.gif_url;
        document.getElementById('resultLink').href = data.gif_url;
      }
      // 예시: 오류 메시지 표시
      if (data.status === 'failed' && data.message) {
        document.getElementById('errorMessage').innerText = `오류: ${data.message}`;
      }
    });
    ```

*   **`pipeline_log` 이벤트**: 파이프라인 실행 중 발생하는 상세 로그 메시지를 실시간으로 표시합니다.
    ```javascript
    socket.on('pipeline_log', (data) => {
      console.log('Pipeline Log:', data.message);
      const logWindow = document.getElementById('logWindow');
      const newLogEntry = document.createElement('p');
      newLogEntry.innerText = data.message;
      logWindow.appendChild(newLogEntry);
      logWindow.scrollTop = logWindow.scrollHeight; // 스크롤을 항상 최신 로그로 이동
    });
    ```

### 4.2. UI 요소 연결 가이드
*   **진행률 바**: `pipeline_status` 이벤트의 `progress` 필드를 사용하여 너비를 조절하고 텍스트를 업데이트합니다.
*   **로그 창**: `pipeline_log` 이벤트의 `message` 필드를 받아 새로운 줄을 추가하고 스크롤을 관리합니다.
*   **현재 단계 표시**: `pipeline_status` 이벤트의 `current_step` 필드를 사용하여 현재 파이프라인 단계를 사용자에게 알립니다.
*   **결과 표시**: `pipeline_status` 이벤트의 `status`가 `completed`일 때 `gif_url`을 받아 최종 결과물(GIF)을 표시합니다.
*   **오류 메시지**: `pipeline_status` 이벤트의 `status`가 `failed`일 때 `message` 필드를 받아 사용자에게 오류 내용을 알립니다.

---