# providers/mock_provider.py

"""
CRENOBA Mock Provider

v0.7.2 목표:
- 실제 AI API 호출 없이 Agent 출력 구조를 테스트한다.
- /crenoba task 입력 시 사용자의 할 일을 직접 분석한다.
- 입력된 작업을 중요도 / 긴급도 / 예상 소요시간 기준으로 분류한다.
"""


# ============================================================
# 공통 유틸
# ============================================================

def _extract_user_input(prompt: str) -> str:
    """
    prompt 안에서 '사용자의 입력' 부분을 최대한 추출한다.
    mock 응답에서 사용자의 원래 요청을 보여주기 위한 보조 함수다.
    """
    if not prompt:
        return ""

    marker = "## 사용자의 입력"
    if marker not in prompt:
        return prompt.strip()

    after_marker = prompt.split(marker, 1)[1].strip()

    stop_markers = [
        "## 역할",
        "## 출력",
        "## 답변",
        "## 출력 형식",
    ]

    for stop in stop_markers:
        if stop in after_marker:
            after_marker = after_marker.split(stop, 1)[0].strip()
            break

    return after_marker.strip()


def _clean_task_line(line: str) -> str:
    """
    사용자가 입력한 할 일 줄에서 -, *, 숫자. 같은 기호를 제거한다.
    """
    cleaned = line.strip()

    prefixes = ["-", "*", "•", "·"]

    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()

    # 1. 할 일 / 1) 할 일 형태 제거
    if len(cleaned) >= 3:
        first = cleaned[0]
        second = cleaned[1]

        if first.isdigit() and second in [".", ")"]:
            cleaned = cleaned[2:].strip()

    return cleaned


def _parse_tasks(user_input: str) -> list[str]:
    """
    사용자의 입력에서 할 일 후보를 추출한다.
    줄 단위로 분석하고, 비어 있거나 제목에 가까운 문장은 제외한다.
    """
    if not user_input:
        return []

    ignore_lines = [
        "오늘 해야 할 일",
        "해야 할 일",
        "할 일",
        "task",
        "사용자가 구체적인 할 일을 입력하지 않았음",
    ]

    tasks = []

    for raw_line in user_input.splitlines():
        line = _clean_task_line(raw_line)

        if not line:
            continue

        normalized = line.replace(":", "").strip()

        if normalized in ignore_lines:
            continue

        if line.startswith("/crenoba"):
            continue

        # 너무 긴 문장은 설명일 가능성이 있으므로 그대로 하나의 작업 후보로 넣되,
        # 앞뒤 공백만 정리한다.
        tasks.append(line)

    if not tasks and user_input.strip():
        tasks.append(user_input.strip())

    return tasks


def _estimate_minutes(task: str) -> int:
    """
    작업 이름을 기준으로 대략적인 예상 소요시간을 계산한다.
    mock 단계이므로 규칙 기반으로 처리한다.
    """
    lowered = task.lower()

    short_keywords = [
        "git",
        "push",
        "commit",
        "status",
        "확인",
        "정리",
        "메모",
        "copy",
        "복사",
    ]

    medium_keywords = [
        "수정",
        "테스트",
        "실행",
        "ui",
        "버튼",
        "provider",
        "prompt",
        "프롬프트",
        "과제",
    ]

    long_keywords = [
        "고도화",
        "리팩토링",
        "구현",
        "개발",
        "보고서",
        "발표",
        "프로젝트",
        "시험",
        "공부",
        "apollo",
        "opencv",
        "arduino",
    ]

    if any(keyword in lowered for keyword in short_keywords):
        return 30

    if any(keyword in lowered for keyword in long_keywords):
        return 90

    if any(keyword in lowered for keyword in medium_keywords):
        return 60

    return 45


def _classify_task(task: str) -> str:
    """
    작업을 must / optional / later 중 하나로 분류한다.
    """
    lowered = task.lower()

    must_keywords = [
        "마감",
        "제출",
        "오늘",
        "반드시",
        "꼭",
        "필수",
        "에러",
        "오류",
        "버그",
        "push",
        "commit",
        "github",
        "테스트",
        "실행",
        "업로드",
    ]

    later_keywords = [
        "나중",
        "추후",
        "언젠가",
        "아이디어",
        "디자인",
        "꾸미기",
        "선택",
        "여유",
        "시간 남으면",
    ]

    optional_keywords = [
        "정리",
        "메모",
        "개선",
        "보완",
        "자료",
        "복습",
        "확인",
    ]

    if any(keyword in lowered for keyword in must_keywords):
        return "must"

    if any(keyword in lowered for keyword in later_keywords):
        return "later"

    if any(keyword in lowered for keyword in optional_keywords):
        return "optional"

    return "optional"


def _analyze_tasks(tasks: list[str]) -> dict:
    """
    task 목록을 받아서 분류 결과를 만든다.
    """
    result = {
        "must": [],
        "optional": [],
        "later": [],
    }

    for task in tasks:
        category = _classify_task(task)
        minutes = _estimate_minutes(task)

        result[category].append({
            "title": task,
            "minutes": minutes,
        })

    # 반드시 해야 할 일이 하나도 없으면 첫 번째 작업을 must로 올린다.
    if not result["must"] and result["optional"]:
        first_task = result["optional"].pop(0)
        result["must"].append(first_task)

    return result


def _format_task_items(items: list[dict]) -> str:
    """
    작업 리스트를 markdown 번호 목록으로 만든다.
    """
    if not items:
        return "- 없음"

    lines = []

    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item['title']} — 예상 {item['minutes']}분")

    return "\n".join(lines)


def _make_30min_plan(analysis: dict) -> str:
    """
    must 작업을 중심으로 30분 단위 실행 계획을 만든다.
    """
    ordered_tasks = analysis["must"] + analysis["optional"] + analysis["later"]

    if not ordered_tasks:
        return """
### 0분 ~ 30분
- 오늘 해야 할 일을 먼저 3개 이상 적는다.

### 30분 ~ 60분
- 가장 중요한 작업 1개를 골라 시작한다.
""".strip()

    blocks = []
    current_start = 0

    for task in ordered_tasks:
        remaining = task["minutes"]
        first_block = True

        while remaining > 0:
            current_end = current_start + 30

            if first_block:
                action = task["title"]
                first_block = False
            else:
                action = f"{task['title']} 이어서 진행"

            blocks.append(
                f"### {current_start}분 ~ {current_end}분\n"
                f"- {action}"
            )

            current_start = current_end
            remaining -= 30

            if len(blocks) >= 6:
                break

        if len(blocks) >= 6:
            break

    return "\n\n".join(blocks)


def _get_next_action(analysis: dict) -> str:
    """
    지금 바로 할 다음 행동 1개를 정한다.
    """
    if analysis["must"]:
        first = analysis["must"][0]["title"]
        return f"지금 바로 **{first}** 작업을 열고, 30분 동안 진행할 수 있는 첫 단계부터 시작하세요."

    if analysis["optional"]:
        first = analysis["optional"][0]["title"]
        return f"지금 바로 **{first}** 작업부터 가볍게 시작하세요."

    return "지금 바로 오늘 해야 할 일을 3개만 적으세요."


# ============================================================
# Agent별 mock 응답
# ============================================================

def _mock_task_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)
    tasks = _parse_tasks(user_input)
    analysis = _analyze_tasks(tasks)

    must_text = _format_task_items(analysis["must"])
    optional_text = _format_task_items(analysis["optional"])
    later_text = _format_task_items(analysis["later"])
    plan_text = _make_30min_plan(analysis)
    next_action = _get_next_action(analysis)

    total_minutes = sum(
        item["minutes"]
        for group in analysis.values()
        for item in group
    )

    if analysis["must"]:
        core_goal = analysis["must"][0]["title"]
    elif tasks:
        core_goal = tasks[0]
    else:
        core_goal = "오늘 해야 할 일을 명확히 정리하기"

    return f"""
# CRENOBA Task Agent v0.7.2

입력 내용:
{user_input}

---

## 1. 오늘의 핵심 목표

오늘의 핵심 목표는 **{core_goal}** 작업을 중심으로 실제로 끝낼 수 있는 실행 계획을 만드는 것입니다.

---

## 2. 반드시 해야 할 일

{must_text}

---

## 3. 시간이 남으면 할 일

{optional_text}

---

## 4. 미뤄도 되는 일

{later_text}

---

## 5. 30분 단위 실행 계획

{plan_text}

---

## 6. 다음 행동 1개

{next_action}

---

## 7. 마무리 체크 질문

- 오늘 반드시 해야 할 일을 실제로 끝냈는가?
- 남은 작업이 다음에 바로 이어서 할 수 있을 만큼 정리되었는가?
- GitHub에 올려야 할 변경 사항이 있다면 commit과 push까지 완료했는가?

---

## 작업량 요약

- 감지된 작업 수: {len(tasks)}개
- 예상 총 작업 시간: 약 {total_minutes}분
- 우선 처리 작업 수: {len(analysis["must"])}개
""".strip()


def _mock_study_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)

    return f"""
# CRENOBA Study Agent

입력 내용:
{user_input}

## 1. 공부 목표
오늘 공부할 내용을 이해 가능한 단위로 나누고, 핵심 개념을 먼저 잡는 것이 목표입니다.

## 2. 핵심 개념
- 주요 개념 정리
- 공식 또는 원리 확인
- 예제 풀이

## 3. 이해해야 할 순서
1. 개념 읽기
2. 공식 의미 확인
3. 예제 따라 풀기
4. 혼자 다시 풀기

## 4. 오늘 공부 계획
- 30분: 개념 정리
- 30분: 예제 풀이
- 30분: 오답 확인

## 5. 확인 문제
- 이 개념을 한 문장으로 설명할 수 있는가?
- 공식이 어디서 나왔는지 이해했는가?
""".strip()


def _mock_code_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)

    return f"""
# CRENOBA Code Agent

입력 내용:
{user_input}

## 1. 문제 요약
입력된 코드 작업 또는 오류를 기준으로 문제를 분석해야 합니다.

## 2. 원인 분석
- 에러 메시지 확인
- 관련 파일 확인
- 함수 이름, import, 경로 문제 확인

## 3. 해결 방향
1. 에러가 발생한 줄 찾기
2. 관련 함수나 변수 확인하기
3. 수정 후 다시 실행하기

## 4. 수정 코드
현재는 mock provider 단계이므로 실제 코드 수정은 입력된 코드 확인 후 진행합니다.

## 5. 테스트 방법
- 서버 실행
- 브라우저 접속
- 기능 클릭 테스트
- 터미널 에러 확인
""".strip()


def _mock_report_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)

    return f"""
# CRENOBA Report Agent

입력 내용:
{user_input}

## 1. 문서 목적
입력한 주제나 자료를 바탕으로 보고서나 발표자료의 목적을 먼저 정리합니다.

## 2. 핵심 내용
- 반드시 들어가야 할 내용
- 근거 자료
- 결과 또는 결론

## 3. 추천 구성
1. 제목
2. 배경
3. 본론
4. 결과
5. 결론
6. 참고자료

## 4. 초안
현재는 mock provider 단계입니다.
실제 보고서 초안은 입력 내용이 더 구체화되면 생성합니다.

## 5. 보완할 점
- 제출 형식
- 분량
- 대상 독자
- 필요한 그림이나 표
""".strip()


def _mock_project_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)

    return f"""
# CRENOBA Project Agent

입력 내용:
{user_input}

## 1. 현재 프로젝트 상태
프로젝트 진행 상황을 기준으로 완료, 진행 중, 다음 작업을 분리해야 합니다.

## 2. 완료된 작업
- 현재까지 끝난 기능 정리

## 3. 남은 작업
- 아직 구현되지 않은 기능 정리

## 4. 우선순위
1. 실행 가능한 핵심 기능
2. 오류 수정
3. 사용성 개선
4. 기록 및 정리

## 5. 다음 단계
가장 작은 다음 작업 1개를 정해서 진행합니다.
""".strip()


def _mock_apollo_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)

    return f"""
# CRENOBA Apollo Agent

입력 내용:
{user_input}

## 1. Apollo 작업 요약
자율주행, OpenCV, Arduino 모터 제어 관련 작업을 분석합니다.

## 2. 현재 문제
입력된 문제를 기준으로 하드웨어, 코드, 제어 로직을 나누어 확인해야 합니다.

## 3. 원인 후보
- 배선 문제
- 파라미터 계산 문제
- 코드 로직 문제
- 센서 또는 드라이버 설정 문제

## 4. 해결 단계
1. 현재 증상 확인
2. 코드와 배선 분리해서 점검
3. 작은 테스트 코드로 검증
4. 전체 코드에 반영

## 5. 테스트 방법
- Serial Monitor 출력 확인
- 입력 각도 테스트
- INPOS 신호 확인
- 비상정지 동작 확인
""".strip()


def _mock_relay_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)

    return f"""
# CRENOBA Relay Agent

입력 내용:
{user_input}

## 1. 현재 버전
CRENOBA v0.7.x

## 2. 완료된 작업
- Core Agent 기본 구조
- mock provider 연결
- Web UI 연결
- Task Agent 고도화 진행

## 3. 중요한 결정
- CRENOBA는 브랜드형 챗봇이 아니라 목적별 업무 보조 Agent 시스템이다.
- /crenoba 명령어로 Agent를 실행한다.
- /gpt 명령어는 ChatGPT 작업 정리와 인수인계에 사용한다.

## 4. 현재 문제
현재 mock provider 기반으로 Agent 응답 구조를 테스트 중입니다.

## 5. 다음 작업
- Task Agent 입력 분석 고도화
- Code Agent 고도화
- Project Agent 고도화
- 실제 AI Provider 연결 안정화

## 6. 새 채팅 인수인계 문서
다음 채팅에서는 /gpt restore로 이 내용을 복원하고, 이어서 CRENOBA Agent 고도화를 진행하면 됩니다.
""".strip()


def _mock_default_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)

    return f"""
# CRENOBA Mock Response

입력 내용:
{user_input}

현재 mock provider가 정상 작동 중입니다.
Agent별 고도화는 v0.7부터 순서대로 진행합니다.
""".strip()


# ============================================================
# Provider 진입점
# ============================================================

def generate_response(prompt: str) -> str:
    """
    main.py 또는 ai_client.py에서 호출할 수 있는 mock 응답 함수.
    """
    if not prompt:
        return _mock_default_response("")

    if "CRENOBA TASK AGENT" in prompt:
        return _mock_task_response(prompt)

    if "CRENOBA STUDY AGENT" in prompt:
        return _mock_study_response(prompt)

    if "CRENOBA CODE AGENT" in prompt:
        return _mock_code_response(prompt)

    if "CRENOBA REPORT AGENT" in prompt:
        return _mock_report_response(prompt)

    if "CRENOBA PROJECT AGENT" in prompt:
        return _mock_project_response(prompt)

    if "CRENOBA APOLLO AGENT" in prompt:
        return _mock_apollo_response(prompt)

    if "CRENOBA RELAY AGENT" in prompt:
        return _mock_relay_response(prompt)

    return _mock_default_response(prompt)


class MockProvider:
    """
    Mock Provider 클래스.
    ai_client.py에서 class 방식으로 호출해도 동작하도록 유지한다.
    """

    def generate(self, prompt: str) -> str:
        return generate_response(prompt)

    def call(self, prompt: str) -> str:
        return generate_response(prompt)

    def run(self, prompt: str) -> str:
        return generate_response(prompt)