def generate(prompt: str):
    if "CRENOBA Task Agent" in prompt:
        output = """
# CRENOBA Task Agent Mock Response

1. 오늘의 핵심 목표
CRENOBA Core Agent를 업무 보조용 Agent 시스템으로 전환한다.

2. 우선순위 정리
- 1순위: 명령어 체계를 업무 중심으로 변경
- 2순위: mock provider 응답을 Agent별로 변경
- 3순위: 웹 UI 버튼을 업무 Agent 중심으로 변경
- 4순위: 실제 AI Provider 연결 준비

3. 1시간 안에 할 일
- prompt_builder.py 수정
- mock_provider.py 수정
- index.html 버튼 문구 수정
- app.js 예시 명령어 수정
- 웹 UI에서 /crenoba task 테스트

4. 나중에 해도 되는 일
- UI 디자인 추가 개선
- 실제 OpenAI API 연결
- 로그인/계정 기능
- 데이터베이스 저장

5. 바로 다음 행동
/crenoba task 버튼을 눌러 입력창이 바뀌는지 확인하고 Run Agent를 실행한다.
"""

    elif "CRENOBA Study Agent" in prompt:
        output = """
# CRENOBA Study Agent Mock Response

1. 개념 한 줄 요약
Study Agent는 전공 공부, 과제, 개념 정리를 도와주는 학습 보조 Agent다.

2. 핵심 개념 설명
사용자가 어려운 개념을 입력하면 핵심 정의, 공식, 풀이 흐름, 헷갈리는 부분을 나누어 설명한다.

3. 중요한 공식 또는 원리
공식이 필요한 과목에서는 단순 암기가 아니라 언제 쓰는지까지 설명해야 한다.

4. 자주 헷갈리는 부분
- 정의만 외우고 실제 문제 적용을 못 하는 경우
- 공식의 조건을 확인하지 않는 경우
- 단위와 부호를 놓치는 경우

5. 예시 또는 풀이 흐름
문제 조건 확인 → 필요한 개념 선택 → 공식 적용 → 단위 확인 → 결과 해석

6. 다음 공부 방향
열역학, 유체역학, 제어, 기계공학 과목별 템플릿을 추가한다.
"""

    elif "CRENOBA Code Agent" in prompt:
        output = """
# CRENOBA Code Agent Mock Response

1. 문제 또는 목표 요약
Code Agent는 사용자의 개발, 디버깅, 리팩토링을 보조한다.

2. 원인/구현 방향 분석
현재 CRENOBA는 FastAPI + Provider 구조 + Web UI로 구성되어 있으며, command에 따라 Agent를 선택한다.

3. 수정 또는 구현 방법
기능을 추가할 때는 다음 순서로 진행한다:
- prompt_builder.py에 Agent 추가
- mock_provider.py에 테스트 응답 추가
- app.js에 예시 추가
- index.html에 버튼 추가

4. 필요한 코드
현재는 mock 단계이므로 실제 API 호출보다 구조 안정화가 우선이다.

5. 테스트 방법
- 웹 UI 접속
- /crenoba code 입력
- Run Agent 클릭
- provider=mock, agent=CRENOBA Code Agent 확인

6. 다음 개발 단계
OpenAI 연결 전, Agent별 입력/출력 구조를 먼저 확정한다.
"""

    elif "CRENOBA Report Agent" in prompt:
        output = """
# CRENOBA Report Agent Mock Response

1. 문서 목적
Report Agent는 보고서, 발표 자료, 과제 제출용 문서를 빠르게 초안화하기 위한 Agent다.

2. 추천 제목
CRENOBA 업무 보조 AI Agent 시스템 설계

3. 목차
1. 개발 배경
2. 시스템 목표
3. Agent 명령어 구조
4. 기술 스택
5. 현재 구현 상태
6. 향후 계획

4. 본문 초안
CRENOBA는 사용자의 반복적인 업무와 프로젝트 작업을 보조하기 위한 AI Agent 시스템이다. 초기 목표는 브랜드형 챗봇이 아니라, 목적별 Agent를 통해 과제, 코드, 보고서, 프로젝트 관리, 자율주행 개발을 지원하는 것이다.

5. 표/그림 제안
- Agent 종류별 역할 표
- FastAPI 요청 흐름도
- Provider 구조 다이어그램

6. 결론 또는 마무리 문장
CRENOBA는 단순한 AI 응답 도구가 아니라, 사용자의 작업을 실행 가능한 결과물로 바꾸는 업무 보조 시스템을 목표로 한다.
"""

    elif "CRENOBA Project Agent" in prompt:
        output = """
# CRENOBA Project Agent Mock Response

1. 프로젝트 목표 요약
CRENOBA를 목적별 AI Agent들이 사용자의 업무를 보조하는 로컬 웹 기반 시스템으로 만든다.

2. 현재 단계
v0.6: 업무 보조 Agent 명령어 체계로 리팩토링 중이다.

3. 이번 주 목표
- task/study/code/report/project/apollo/relay 명령어 적용
- 웹 UI 버튼 교체
- mock provider 테스트 완료
- 실제 AI Provider 연결 준비

4. 다음 개발 순서
1. 업무 Agent 명령어 적용
2. UI 테스트
3. OpenAI Provider 연결 준비
4. 비용 절약용 mock fallback 유지
5. 간단한 작업 기록 저장 기능 강화

5. 막힌 문제 또는 리스크
- Gemini API는 현재 403/429 문제로 실제 호출이 어려움
- OpenAI API는 ChatGPT Plus와 별도 과금
- Agent가 많아질수록 명령어 구조 관리가 필요함

6. 완료 기준
웹 UI에서 모든 업무 Agent 버튼이 정상 작동하고, 각 Agent 이름과 mock 응답이 정확히 출력된다.
"""

    elif "CRENOBA Apollo Agent" in prompt:
        output = """
# CRENOBA Apollo Agent Mock Response

1. Apollo 작업 목표
자율주행 프로젝트에서 OpenCV 차선 인식, ROS2, Arduino 모터 제어 작업을 보조한다.

2. 현재 문제 또는 주제
Apollo Agent는 자율주행 관련 작업을 CRENOBA 내부 전용 Agent로 분리하기 위한 기능이다.

3. 기술 흐름 정리
- OpenCV: 차선 인식, ROI, BEV, HSV/HLS 마스크, Sliding Window, Polyfit
- ROS2: 이미지 토픽, cv_bridge, 노드 구조
- Arduino: 브레이크 모터 제어, pulse/dir, encoder monitor
- 문서화: 발표/보고서용 파이프라인 정리

4. 구현/수정 방향
Apollo 관련 질문은 일반 code Agent보다 Apollo Agent에서 처리하도록 한다.

5. 테스트 방법
웹 UI에서 /crenoba apollo 명령어를 실행하고 Apollo Agent가 선택되는지 확인한다.

6. 다음 실험 또는 개발 단계
차선 인식 파이프라인 템플릿과 브레이크 모터 제어 템플릿을 Apollo Agent에 추가한다.
"""

    elif "CRENOBA Relay Agent" in prompt:
        output = """
# CRENOBA Relay Document

1. 현재 목표
CRENOBA를 브랜드형 챗봇이 아니라 업무 보조용 목적별 AI Agent 시스템으로 전환한다.

2. 현재 버전
CRENOBA Core Agent v0.6

3. 완료된 작업
- FastAPI 서버 구축
- /agent API 구현
- Provider 교체 구조 구현
- Gemini/OpenAI/Mock Provider 구조 설계
- Mock Provider 정상 작동 확인
- 웹 UI 구축
- /gpt와 /crenoba 명령어 역할 분리
- 버튼 동작 문제 해결
- 업무 보조 Agent 체계로 방향 재정의

4. 결정된 명령어 체계
ChatGPT 대화용:
- /gpt

CRENOBA 앱 내부용:
- /crenoba task
- /crenoba study
- /crenoba code
- /crenoba report
- /crenoba project
- /crenoba apollo
- /crenoba relay

5. 현재 코드/기술 구조
- Backend: FastAPI
- Frontend: HTML/CSS/JavaScript
- Config: python-dotenv
- Provider:
  - mock
  - gemini
  - openai

6. 미해결 문제
- 실제 OpenAI API 연결 전
- Gemini API 403/429 문제
- 업무 Agent별 실제 프롬프트 고도화 필요
- 작업 결과 저장 방식 미정

7. 다음 작업
1. 웹 UI 버튼을 업무 Agent 중심으로 변경
2. 모든 /crenoba 명령어 테스트
3. OpenAI Provider 실제 연결 준비
4. 작업 기록 저장 기능 강화

8. 다음 채팅 시작 명령어
/gpt restore
CRENOBA Core Agent v0.6 업무 보조 Agent 시스템을 이어서 진행하자.
"""

    else:
        output = """
# CRENOBA General Mock Response

현재 CRENOBA 업무 보조 Agent 시스템이 mock provider로 실행 중입니다.

사용 가능한 명령어:
- /crenoba task
- /crenoba study
- /crenoba code
- /crenoba report
- /crenoba project
- /crenoba apollo
- /crenoba relay

다음 단계:
웹 UI에서 각 명령어 버튼을 테스트하고 Agent 이름과 응답이 올바르게 출력되는지 확인합니다.
"""

    return {
        "provider": "mock",
        "source": "mock",
        "model": "mock-agent-v0.6",
        "output": output,
        "error": None,
    }