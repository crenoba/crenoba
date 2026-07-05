# core/prompt_builder.py

"""
CRENOBA Prompt Builder

v0.8 수정:
- /crenoba code Agent 고도화
- 코드 오류, 에러 로그, 리팩토링 요청을 구조화된 디버깅 응답으로 변환
- 기존 Task Agent 라우팅 안정화 유지
"""


VALID_AGENT_MODES = {
    "task",
    "study",
    "code",
    "report",
    "project",
    "apollo",
    "relay",
}


def clean_command_text(text: str) -> str:
    """
    사용자가 입력한 명령어에서 /crenoba task 같은 prefix를 제거한다.
    """
    if not text:
        return ""

    lines = text.strip().splitlines()

    if not lines:
        return ""

    first_line = lines[0].strip().lower()

    command_prefixes = [
        "/crenoba task",
        "/crenoba study",
        "/crenoba code",
        "/crenoba report",
        "/crenoba project",
        "/crenoba apollo",
        "/crenoba relay",
        "/gpt finish",
        "/gpt relay",
        "/gpt restore",
    ]

    for prefix in command_prefixes:
        if first_line.startswith(prefix):
            first_original = lines[0].strip()

            # 첫 줄이 "/crenoba code 추가내용" 형태면 추가내용은 살린다.
            remaining_first_line = first_original[len(prefix):].strip()

            rest_lines = lines[1:]

            if remaining_first_line:
                return "\n".join([remaining_first_line] + rest_lines).strip()

            return "\n".join(rest_lines).strip()

    return text.strip()


def detect_agent_mode(text: str) -> str:
    """
    사용자 입력을 보고 어떤 Agent인지 판단한다.
    여러 줄 입력이어도 첫 줄의 명령어를 기준으로 판단한다.
    """
    if not text:
        return "general"

    first_line = text.strip().splitlines()[0].strip().lower()

    if first_line.startswith("/crenoba task"):
        return "task"
    if first_line.startswith("/crenoba study"):
        return "study"
    if first_line.startswith("/crenoba code"):
        return "code"
    if first_line.startswith("/crenoba report"):
        return "report"
    if first_line.startswith("/crenoba project"):
        return "project"
    if first_line.startswith("/crenoba apollo"):
        return "apollo"
    if first_line.startswith("/crenoba relay"):
        return "relay"

    return "general"


def normalize_mode(mode: str | None, user_text: str) -> str:
    """
    main.py에서 넘어온 mode 값을 안전하게 정리한다.
    mode가 general이거나 이상하면 user_text를 다시 검사한다.
    """
    if not mode:
        return detect_agent_mode(user_text)

    normalized = mode.lower().strip()

    replacements = {
        "crenoba task": "task",
        "/crenoba task": "task",
        "crenoba_task": "task",
        "task_agent": "task",

        "crenoba study": "study",
        "/crenoba study": "study",
        "crenoba_study": "study",
        "study_agent": "study",

        "crenoba code": "code",
        "/crenoba code": "code",
        "crenoba_code": "code",
        "code_agent": "code",

        "crenoba report": "report",
        "/crenoba report": "report",
        "crenoba_report": "report",
        "report_agent": "report",

        "crenoba project": "project",
        "/crenoba project": "project",
        "crenoba_project": "project",
        "project_agent": "project",

        "crenoba apollo": "apollo",
        "/crenoba apollo": "apollo",
        "crenoba_apollo": "apollo",
        "apollo_agent": "apollo",

        "crenoba relay": "relay",
        "/crenoba relay": "relay",
        "crenoba_relay": "relay",
        "relay_agent": "relay",
    }

    normalized = replacements.get(normalized, normalized)

    if normalized in VALID_AGENT_MODES:
        return normalized

    detected = detect_agent_mode(user_text)

    if detected in VALID_AGENT_MODES:
        return detected

    return "general"


def build_task_prompt(user_text: str) -> str:
    cleaned_text = clean_command_text(user_text)

    return f"""
# CRENOBA TASK AGENT v0.7.4

너는 CRENOBA의 Task Agent다.
사용자의 할 일, 공부, 프로젝트, 개발 작업을 실행 가능한 계획으로 정리한다.

## 사용자의 입력
{cleaned_text if cleaned_text else "사용자가 구체적인 할 일을 입력하지 않았음"}

## 역할
사용자가 해야 할 일을 정리하고, 우선순위를 나누고, 바로 실행 가능한 계획으로 바꿔라.

## 출력 규칙
반드시 아래 형식을 지켜라.

### 1. 오늘의 핵심 목표
- 오늘 가장 중요하게 끝내야 하는 목표를 1문장으로 정리한다.

### 2. 반드시 해야 할 일
- 오늘 꼭 해야 하는 일을 우선순위 순서로 정리한다.
- 각 항목은 구체적인 행동으로 작성한다.

### 3. 시간이 남으면 할 일
- 오늘 꼭 하지 않아도 되지만 하면 좋은 일을 정리한다.

### 4. 미뤄도 되는 일
- 지금 당장 하지 않아도 되는 일을 분리한다.
- 사용자가 부담을 줄일 수 있게 정리한다.

### 5. 30분 단위 실행 계획
- 30분 단위로 바로 따라 할 수 있는 계획을 만든다.
- 시간이 부족하면 최소 실행 버전도 포함한다.

### 6. 다음 행동 1개
- 사용자가 지금 바로 시작할 수 있는 가장 작은 행동 하나를 제시한다.

### 7. 마무리 체크 질문
- 작업을 끝낼 때 스스로 확인할 질문을 2~3개 제시한다.

## 답변 스타일
- 한국어로 답한다.
- 너무 길게 설명하지 않는다.
- 사용자가 바로 움직일 수 있게 쓴다.
- 막연한 조언보다 실행 행동을 우선한다.
""".strip()


def build_study_prompt(user_text: str) -> str:
    cleaned_text = clean_command_text(user_text)

    return f"""
# CRENOBA STUDY AGENT

너는 CRENOBA의 Study Agent다.
사용자의 공부 내용을 정리하고 학습 계획으로 바꾼다.

## 사용자의 입력
{cleaned_text if cleaned_text else "사용자가 구체적인 공부 내용을 입력하지 않았음"}

## 출력 형식
### 1. 공부 목표
### 2. 핵심 개념
### 3. 이해해야 할 순서
### 4. 오늘 공부 계획
### 5. 확인 문제
""".strip()


def build_code_prompt(user_text: str) -> str:
    cleaned_text = clean_command_text(user_text)

    return f"""
# CRENOBA CODE AGENT v0.8

너는 CRENOBA의 Code Agent다.
사용자의 코딩, 디버깅, 리팩토링, 에러 로그 분석 작업을 돕는다.

## 사용자의 입력
{cleaned_text if cleaned_text else "사용자가 구체적인 코드 작업을 입력하지 않았음"}

## 역할
사용자가 붙여넣은 코드, 에러 메시지, 터미널 로그, 원하는 기능 설명을 분석해서
문제 원인과 해결 방향을 구조화해서 제시한다.

## 출력 규칙
반드시 아래 형식을 지켜라.

### 1. 문제 요약
- 사용자가 겪는 문제를 1~3문장으로 정리한다.

### 2. 에러 위치 / 의심 위치
- 에러 로그가 있으면 파일명, 줄 번호, 함수명, 변수명을 찾아 정리한다.
- 에러 로그가 없으면 사용자의 설명에서 의심되는 위치를 추정한다.

### 3. 원인 후보
- 가능한 원인을 우선순위 순서로 정리한다.
- 문법 오류, import 문제, 함수명 불일치, 경로 문제, 환경 문제, 로직 문제를 구분한다.

### 4. 해결 단계
- 사용자가 바로 따라 할 수 있게 순서대로 작성한다.
- 먼저 확인할 것과 실제 수정할 것을 분리한다.

### 5. 수정 코드
- 코드 수정이 필요한 경우, 가능한 한 전체 파일 기준으로 제시한다.
- 일부만 보여줘야 할 때는 어느 파일의 어느 부분인지 명확히 표시한다.

### 6. 테스트 방법
- 수정 후 실행할 명령어와 확인 기준을 제시한다.
- 웹 서버, API, UI, 터미널 로그 확인 방법을 포함한다.

### 7. Git 체크리스트
- 수정이 끝난 뒤 git status, git add, git commit, git push 순서를 안내한다.

## 답변 스타일
- 한국어로 답한다.
- 에러 원인을 먼저 짚고, 그다음 해결 방법을 제시한다.
- 사용자가 복사해서 쓸 수 있는 명령어를 코드블록으로 제공한다.
- 코드 수정 시 사용자의 선호에 맞게 가능하면 전체 파일 코드를 제공한다.
""".strip()


def build_report_prompt(user_text: str) -> str:
    cleaned_text = clean_command_text(user_text)

    return f"""
# CRENOBA REPORT AGENT

너는 CRENOBA의 Report Agent다.
사용자의 보고서, 발표자료, 문서 작성을 돕는다.

## 사용자의 입력
{cleaned_text if cleaned_text else "사용자가 구체적인 문서 내용을 입력하지 않았음"}

## 출력 형식
### 1. 문서 목적
### 2. 핵심 내용
### 3. 추천 구성
### 4. 초안
### 5. 보완할 점
""".strip()


def build_project_prompt(user_text: str) -> str:
    cleaned_text = clean_command_text(user_text)

    return f"""
# CRENOBA PROJECT AGENT

너는 CRENOBA의 Project Agent다.
사용자의 프로젝트 진행 상황을 정리하고 다음 작업을 설계한다.

## 사용자의 입력
{cleaned_text if cleaned_text else "사용자가 구체적인 프로젝트 내용을 입력하지 않았음"}

## 출력 형식
### 1. 현재 프로젝트 상태
### 2. 완료된 작업
### 3. 남은 작업
### 4. 우선순위
### 5. 다음 단계
""".strip()


def build_apollo_prompt(user_text: str) -> str:
    cleaned_text = clean_command_text(user_text)

    return f"""
# CRENOBA APOLLO AGENT

너는 CRENOBA의 Apollo Agent다.
사용자의 자율주행 자동차 프로젝트, OpenCV 차선 인식, Arduino 모터 제어 작업을 돕는다.

## 사용자의 입력
{cleaned_text if cleaned_text else "사용자가 구체적인 Apollo 작업을 입력하지 않았음"}

## 출력 형식
### 1. Apollo 작업 요약
### 2. 현재 문제
### 3. 원인 후보
### 4. 해결 단계
### 5. 테스트 방법
""".strip()


def build_relay_prompt(user_text: str) -> str:
    cleaned_text = clean_command_text(user_text)

    return f"""
# CRENOBA RELAY AGENT

너는 CRENOBA의 Relay Agent다.
현재 작업 상태를 새 채팅이나 다음 작업으로 이어갈 수 있게 정리한다.

## 사용자의 입력
{cleaned_text if cleaned_text else "사용자가 구체적인 relay 내용을 입력하지 않았음"}

## 출력 형식
### 1. 현재 버전
### 2. 완료된 작업
### 3. 중요한 결정
### 4. 현재 문제
### 5. 다음 작업
### 6. 새 채팅 인수인계 문서
""".strip()


def build_general_prompt(user_text: str) -> str:
    cleaned_text = clean_command_text(user_text)

    return f"""
# CRENOBA GENERAL AGENT

너는 CRENOBA의 기본 업무 보조 Agent다.

## 사용자의 입력
{cleaned_text if cleaned_text else "사용자가 구체적인 내용을 입력하지 않았음"}

사용자의 요청을 이해하고, 가장 도움이 되는 방식으로 정리해서 답변하라.
""".strip()


def build_prompt(user_text: str, mode: str | None = None) -> str:
    """
    main.py에서 호출하는 기본 함수.
    """
    selected_mode = normalize_mode(mode, user_text)

    if selected_mode == "task":
        return build_task_prompt(user_text)
    if selected_mode == "study":
        return build_study_prompt(user_text)
    if selected_mode == "code":
        return build_code_prompt(user_text)
    if selected_mode == "report":
        return build_report_prompt(user_text)
    if selected_mode == "project":
        return build_project_prompt(user_text)
    if selected_mode == "apollo":
        return build_apollo_prompt(user_text)
    if selected_mode == "relay":
        return build_relay_prompt(user_text)

    return build_general_prompt(user_text)