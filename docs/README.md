# Effect Stokes

AI 에이전트를 활용하여 사용자 프롬프트로부터 고품질 VFX(시각 효과)를 생성하는 프로젝트입니다.

## 📝 프로젝트 설명

Effect Stokes는 자연어 프롬프트를 입력받아 물리 시뮬레이션, 스타일 적용, 렌더링까지의 복잡한 VFX 파이프라인을 자동화하는 것을 목표로 합니다. LLM(대규모 언어 모델)을 사용하여 Blender 파이썬 스크립트를 동적으로 생성하고, 이를 실행하여 사용자가 원하는 시각 효과를 만들어냅니다.

## ✨ 주요 기능

-   **프롬프트 기반 VFX 생성**: "불꽃펀치, 귀멸풍 스타일"과 같은 간단한 텍스트만으로 VFX 생성 가능
-   **AI 에이전트 시스템**: 시뮬레이션, 스타일, 피드백, 렌더링 등 각 작업을 전문적으로 처리하는 에이전트 기반 아키텍처
-   **동적 코드 생성**: LLM을 활용하여 사용자의 요구사항에 맞는 Blender 스크립트를 실시간으로 생성
-   **자동 피드백 루프**: 생성된 결과물을 평가하고 목표 스타일에 더 가까워지도록 자동으로 렌더링 설정을 조정

## ⚙️ 프로젝트 구조

```
.
├── main.py               # 전체 파이프라인을 관리하는 오케스트레이터
├── simulation_agent.py   # 물리 시뮬레이션 담당 에이전트
├── style_agent.py        # (구현 예정) 시각적 스타일 적용 담당 에이전트
├── feedback_agent.py     # (구현 예정) 결과물 분석 및 피드백 담당 에이전트
├── render_agent.py       # (구현 예정) 최종 렌더링 담당 에이전트
├── llm_interface.py      # LLM과의 통신 모듈
└── prompt_templates.py   # LLM에 사용할 프롬프트 템플릿
```

## 🚀 시작하기

### 사전 준비

-   Python 3.9 이상
-   Blender (환경 변수에 경로 설정 필요)
-   OpenAI API 키

### 실행 방법

1.  **리포지토리 클론:**
    ```bash
    git clone https://github.com/sigongjoa/Effect_Stokes.git
    cd Effect_Stokes
    ```

2.  **필요 라이브러리 설치:**
    ```bash
    pip install openai
    ```

3.  **환경 변수 설정:**
    ```bash
    export OPENAI_API_KEY="YOUR_API_KEY"
    ```

4.  **프로젝트 실행:**
    ```bash
    python main.py
    ```
