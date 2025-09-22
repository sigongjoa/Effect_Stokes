# 테스트 코드 문서 초안

## 1. 개요

본 문서는 `Effect_Stokes` 프로젝트의 테스트 코드에 대한 개요, 각 테스트 파일의 목적, 그리고 테스트 실행 방법을 설명합니다. 프로젝트의 다양한 구성 요소(시뮬레이션 로직, LLM 인터페이스, 하드웨어 감지, 후처리 등)의 기능과 안정성을 보장하기 위한 테스트 전략을 포함합니다.

## 2. 테스트 파일 설명

`tests/` 디렉토리 내의 주요 테스트 파일들은 다음과 같습니다.

### 2.1. `navier_stokes_test.py`
*   **목적**: 프로젝트의 핵심 유체 시뮬레이션 로직인 2D 나비에-스트로크(Navier-Stokes) 솔버의 정확성과 안정성을 검증합니다. 다양한 시뮬레이션 파라미터(예: `grid_resolution`, `viscosity`, `initial_shape_type`)에 따른 유체 거동이 예상대로 작동하는지 확인합니다.
*   **주요 검증 내용**:
    *   파라미터 파싱 및 적용의 유효성.
    *   시뮬레이션 결과 데이터(`u`, `v`, `p` 필드)의 유효성 및 저장.
    *   다양한 초기 조건(vortex, crescent, circle_burst)에서의 시뮬레이션 동작.

### 2.2. `test_flow.py`
*   **목적**: 유체 시뮬레이션의 특정 흐름 패턴이나 상호작용에 대한 테스트를 수행합니다. `navier_stokes_test.py`가 솔버 자체의 기본 기능을 검증한다면, `test_flow.py`는 더 복잡한 유체 흐름 시나리오를 검증하는 데 중점을 둡니다.
*   **주요 검증 내용**:
    *   특정 경계 조건에서의 유체 흐름 패턴.
    *   다중 소스 또는 장애물에 대한 유체 반응.
    *   시간 경과에 따른 유체 역학적 특성 변화.

### 2.3. `test_llm_standalone.py`
*   **목적**: LLM(Large Language Model) 인터페이스(`llm_interface.py`)의 독립적인 기능을 테스트합니다. LLM과의 통신, 프롬프트 구성, 응답 파싱 등이 올바르게 작동하는지 확인합니다.
*   **주요 검증 내용**:
    *   `infer_simulation_and_visualization_parameters` 함수가 유효한 JSON 형식의 파라미터를 반환하는지.
    *   다양한 `effect_description`에 대한 LLM의 파라미터 추론 결과의 일관성 및 유효성.
    *   LLM 통신 오류 및 응답 파싱 오류 처리.

### 2.4. `check_video.py`
*   **목적**: 시뮬레이션 및 렌더링 파이프라인의 최종 결과물인 비디오 또는 이미지 시퀀스의 품질과 정확성을 검증합니다. 주로 후처리 및 시각화 단계의 오류를 감지하는 데 사용됩니다.
*   **주요 검증 내용**:
    *   생성된 비디오/이미지 시퀀스의 존재 여부 및 파일 형식.
    *   비디오의 길이, 프레임 속도, 해상도 등 메타데이터 검증.
    *   (필요시) 특정 프레임의 시각적 내용 또는 특정 요소의 존재 여부.

### 2.5. `gpu_detect_test.py`
*   **목적**: 시스템의 GPU 하드웨어 감지 및 관련 설정이 올바르게 작동하는지 테스트합니다. Blender 렌더링 등 GPU 가속이 필요한 작업 전에 환경을 확인하는 데 중요합니다.
*   **주요 검증 내용**:
    *   GPU 드라이버 및 CUDA(또는 기타 GPU API) 설치 여부.
    *   Blender가 GPU 렌더링 장치를 올바르게 인식하는지.
    *   GPU 사용 가능 여부 및 기본 성능 테스트.

### 2.6. `run_getsuga_tests.py`
*   **목적**: 특정 이펙트(예: "Getsuga Tenshou"와 같은 명명된 이펙트)에 대한 통합 테스트를 수행합니다. 이는 전체 파이프라인이 특정 이펙트 요구사항에 맞춰 올바르게 작동하는지 확인하는 시나리오 기반 테스트입니다.
*   **주요 검증 내용**:
    *   Getsuga 이펙트의 시뮬레이션 파라미터가 올바르게 적용되는지.
    *   Getsuga 이펙트의 시각화 결과가 예상과 일치하는지.
    *   전체 파이프라인을 통한 Getsuga 이펙트 생성의 안정성.

## 3. 테스트 실행 방법

프로젝트의 테스트는 일반적으로 Python의 `pytest` 프레임워크를 사용하여 실행할 수 있습니다.

1.  **가상 환경 활성화**:
    ```bash
    source venv/bin/activate
    ```

2.  **모든 테스트 실행**:
    `tests/` 디렉토리 내의 모든 테스트 파일을 실행합니다.
    ```bash
    pytest tests/
    ```

3.  **특정 테스트 파일 실행**:
    예를 들어, `navier_stokes_test.py`만 실행하려면:
    ```bash
    pytest tests/navier_stokes_test.py
    ```

4.  **특정 테스트 함수 실행**:
    파일 내의 특정 테스트 함수만 실행하려면 `::`를 사용합니다.
    ```bash
    pytest tests/navier_stokes_test.py::test_vortex_simulation
    ```

5.  **상세 결과 보기**:
    `-v` 플래그를 사용하여 더 자세한 테스트 결과를 볼 수 있습니다.
    ```bash
    pytest -v tests/
    ```

6.  **개별 스크립트 직접 실행**:
    일부 테스트 스크립트(예: `navier_stokes_test.py`, `gpu_detect_test.py`)는 `if __name__ == "__main__":` 블록을 포함하여 Python 스크립트로서 직접 실행될 수도 있습니다. 이 경우, 필요한 커맨드 라인 인자를 제공해야 합니다.
    ```bash
    python tests/navier_stokes_test.py <output_directory> <sim_params_json>
    ```

---
