# providers/mock_provider.py

"""
CRENOBA Mock Provider

v0.8 Hotfix
- MockProvider class 복구
- generate_response 진입점 복구
- _mock_code_response 누락 문제 해결
- Task Agent v0.7.4 기능 유지
- Code Agent v0.8 응답 구조 추가
"""


# ============================================================
# 공통 유틸
# ============================================================

def _extract_user_input(prompt: str) -> str:
    """
    Prompt 안에서 '## 사용자의 입력' 아래 내용을 추출한다.
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


def _format_bullet_list(items: list[str]) -> str:
    if not items:
        return "- 없음"

    return "\n".join(f"- {item}" for item in items)


# ============================================================
# Task Agent v0.7.4
# ============================================================

def _clean_task_line(line: str) -> str:
    cleaned = line.strip()

    prefixes = ["-", "*", "•", "·", "□", "☐", "✅", "✔"]

    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()

    if len(cleaned) >= 3:
        first = cleaned[0]
        second = cleaned[1]

        if first.isdigit() and second in [".", ")"]:
            cleaned = cleaned[2:].strip()

    return cleaned.strip()


def _parse_tasks(user_input: str) -> list[str]:
    if not user_input:
        return []

    ignore_lines = {
        "오늘 해야 할 일",
        "해야 할 일",
        "할 일",
        "오늘 할 일",
        "task",
        "todo",
        "to do",
        "사용자가 구체적인 할 일을 입력하지 않았음",
    }

    tasks = []

    for raw_line in user_input.splitlines():
        line = _clean_task_line(raw_line)

        if not line:
            continue

        normalized = line.replace(":", "").strip().lower()

        if normalized in ignore_lines:
            continue

        if line.startswith("/crenoba"):
            continue

        tasks.append(line)

    if not tasks and user_input.strip():
        tasks.append(user_input.strip())

    return tasks


def _estimate_minutes(task: str) -> int:
    lowered = task.lower()

    if any(keyword in lowered for keyword in ["확인", "체크", "메모", "git status"]):
        return 15

    if any(keyword in lowered for keyword in ["git", "push", "commit", "업로드", "정리"]):
        return 30

    if any(keyword in lowered for keyword in ["수정", "테스트", "실행", "ui", "버튼", "prompt", "provider"]):
        return 60

    if any(keyword in lowered for keyword in ["고도화", "리팩토링", "구현", "개발", "보고서", "공부", "시험"]):
        return 90

    return 45


def _detect_task_type(task: str) -> str:
    lowered = task.lower()

    if any(keyword in lowered for keyword in ["git", "push", "commit", "github"]):
        return "Git 관리"

    if any(keyword in lowered for keyword in ["ui", "버튼", "화면", "디자인", "css", "html"]):
        return "UI 작업"

    if any(keyword in lowered for keyword in ["코드", "구현", "리팩토링", "provider", "prompt", "parser", "agent"]):
        return "개발 작업"

    if any(keyword in lowered for keyword in ["테스트", "실행", "확인", "에러", "오류", "버그"]):
        return "검증 작업"

    if any(keyword in lowered for keyword in ["정리", "메모", "문서", "보고서", "발표"]):
        return "정리 작업"

    if any(keyword in lowered for keyword in ["공부", "시험", "과제", "복습"]):
        return "학습 작업"

    return "일반 작업"


def _score_importance(task: str) -> int:
    lowered = task.lower()
    score = 0

    high_keywords = [
        "마감",
        "제출",
        "필수",
        "반드시",
        "꼭",
        "오늘",
        "에러",
        "오류",
        "버그",
        "테스트",
        "실행",
        "github",
        "push",
        "commit",
        "업로드",
    ]

    medium_keywords = [
        "고도화",
        "구현",
        "수정",
        "리팩토링",
        "agent",
        "provider",
        "prompt",
        "ui",
        "버튼",
        "확인",
    ]

    low_keywords = [
        "나중",
        "추후",
        "언젠가",
        "디자인",
        "꾸미기",
        "선택",
        "여유",
    ]

    for keyword in high_keywords:
        if keyword in lowered:
            score += 3

    for keyword in medium_keywords:
        if keyword in lowered:
            score += 2

    for keyword in low_keywords:
        if keyword in lowered:
            score -= 3

    return score


def _score_urgency(task: str) -> int:
    lowered = task.lower()
    score = 0

    urgent_keywords = [
        "오늘",
        "지금",
        "바로",
        "마감",
        "제출",
        "에러",
        "오류",
        "안됨",
        "실패",
        "push",
        "commit",
        "업로드",
    ]

    not_urgent_keywords = [
        "나중",
        "추후",
        "언젠가",
        "시간 남으면",
        "여유",
        "디자인",
        "꾸미기",
    ]

    for keyword in urgent_keywords:
        if keyword in lowered:
            score += 3

    for keyword in not_urgent_keywords:
        if keyword in lowered:
            score -= 3

    return score


def _label_score(score: int) -> str:
    if score >= 5:
        return "높음"

    if score >= 2:
        return "보통"

    return "낮음"


def _classify_task(task: str, importance_score: int, urgency_score: int) -> str:
    lowered = task.lower()

    later_keywords = [
        "나중",
        "추후",
        "언젠가",
        "아이디어",
        "디자인 더",
        "꾸미기",
        "선택",
        "여유",
        "시간 남으면",
    ]

    if any(keyword in lowered for keyword in later_keywords):
        return "later"

    if importance_score >= 4 or urgency_score >= 3:
        return "must"

    if importance_score <= 0 and urgency_score <= 0:
        return "later"

    return "optional"


def _analyze_tasks(tasks: list[str]) -> dict:
    result = {
        "must": [],
        "optional": [],
        "later": [],
    }

    for task in tasks:
        importance_score = _score_importance(task)
        urgency_score = _score_urgency(task)
        minutes = _estimate_minutes(task)
        task_type = _detect_task_type(task)
        category = _classify_task(task, importance_score, urgency_score)

        item = {
            "title": task,
            "minutes": minutes,
            "type": task_type,
            "importance_score": importance_score,
            "urgency_score": urgency_score,
            "importance": _label_score(importance_score),
            "urgency": _label_score(urgency_score),
            "priority_score": importance_score + urgency_score,
        }

        result[category].append(item)

    for key in result:
        result[key].sort(
            key=lambda item: (
                item["priority_score"],
                -item["minutes"],
            ),
            reverse=True,
        )

    if not result["must"] and result["optional"]:
        first_task = result["optional"].pop(0)
        result["must"].append(first_task)

    if not result["must"] and not result["optional"] and not result["later"]:
        result["must"].append({
            "title": "오늘 해야 할 일을 3개 이상 적기",
            "minutes": 15,
            "type": "정리 작업",
            "importance_score": 3,
            "urgency_score": 2,
            "importance": "보통",
            "urgency": "보통",
            "priority_score": 5,
        })

    return result


def _format_task_items(items: list[dict]) -> str:
    if not items:
        return "- 없음"

    lines = []

    for index, item in enumerate(items, start=1):
        lines.append(
            f"{index}. {item['title']}\n"
            f"   - 유형: {item['type']}\n"
            f"   - 중요도: {item['importance']} / 긴급도: {item['urgency']}\n"
            f"   - 예상 시간: {item['minutes']}분"
        )

    return "\n".join(lines)


def _make_30min_plan(analysis: dict) -> str:
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

            if current_start == 0:
                note = "가장 먼저 시작할 작업"
            elif task in analysis["must"]:
                note = "우선 처리 작업"
            elif task in analysis["optional"]:
                note = "시간이 남으면 진행"
            else:
                note = "여유가 있을 때만 진행"

            blocks.append(
                f"### {current_start}분 ~ {current_end}분\n"
                f"- {action}\n"
                f"- 구분: {note}"
            )

            current_start = current_end
            remaining -= 30

            if len(blocks) >= 6:
                break

        if len(blocks) >= 6:
            break

    return "\n\n".join(blocks)


def _get_next_action(analysis: dict) -> str:
    if analysis["must"]:
        first = analysis["must"][0]["title"]
        return f"지금 바로 **{first}** 작업을 열고, 첫 30분 동안 진행할 수 있는 단계부터 시작하세요."

    if analysis["optional"]:
        first = analysis["optional"][0]["title"]
        return f"지금 바로 **{first}** 작업부터 가볍게 시작하세요."

    return "지금 바로 오늘 해야 할 일을 3개만 적으세요."


def _make_summary(analysis: dict) -> str:
    total_tasks = sum(len(group) for group in analysis.values())
    total_minutes = sum(
        item["minutes"]
        for group in analysis.values()
        for item in group
    )

    must_minutes = sum(item["minutes"] for item in analysis["must"])
    optional_minutes = sum(item["minutes"] for item in analysis["optional"])
    later_minutes = sum(item["minutes"] for item in analysis["later"])

    return f"""
- 감지된 작업 수: {total_tasks}개
- 예상 총 작업 시간: 약 {total_minutes}분
- 반드시 해야 할 일: {len(analysis["must"])}개 / 약 {must_minutes}분
- 시간이 남으면 할 일: {len(analysis["optional"])}개 / 약 {optional_minutes}분
- 미뤄도 되는 일: {len(analysis["later"])}개 / 약 {later_minutes}분
""".strip()


def _make_focus_message(analysis: dict) -> str:
    total_minutes = sum(
        item["minutes"]
        for group in analysis.values()
        for item in group
    )

    must_minutes = sum(item["minutes"] for item in analysis["must"])

    if must_minutes >= 180:
        return "오늘은 반드시 해야 할 일만 처리해도 작업량이 많습니다. 선택 작업은 과감히 미루는 것이 좋습니다."

    if total_minutes >= 240:
        return "전체 작업량이 많은 편입니다. 반드시 해야 할 일부터 끝내고, 나머지는 다음 작업으로 넘기는 방식이 안전합니다."

    if total_minutes <= 90:
        return "오늘 작업량은 비교적 가벼운 편입니다. 핵심 작업을 끝낸 뒤 정리와 GitHub 업로드까지 마무리하기 좋습니다."

    return "오늘은 핵심 작업을 먼저 끝내고, 남은 시간에 정리 작업을 붙이는 방식이 좋습니다."


def _mock_task_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)
    tasks = _parse_tasks(user_input)
    analysis = _analyze_tasks(tasks)

    must_text = _format_task_items(analysis["must"])
    optional_text = _format_task_items(analysis["optional"])
    later_text = _format_task_items(analysis["later"])
    plan_text = _make_30min_plan(analysis)
    next_action = _get_next_action(analysis)
    summary_text = _make_summary(analysis)
    focus_message = _make_focus_message(analysis)

    if analysis["must"]:
        core_goal = analysis["must"][0]["title"]
    elif tasks:
        core_goal = tasks[0]
    else:
        core_goal = "오늘 해야 할 일을 명확히 정리하기"

    return f"""
# CRENOBA Task Agent v0.7.4

입력 내용:
{user_input}

---

## 1. 오늘의 핵심 목표

오늘의 핵심 목표는 **{core_goal}** 작업을 먼저 끝내는 것입니다.

운영 전략:
{focus_message}

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

{summary_text}
""".strip()


# ============================================================
# Code Agent v0.8
# ============================================================

def _detect_error_type(user_input: str) -> str:
    lowered = user_input.lower()

    if "syntaxerror" in lowered or "invalid syntax" in lowered:
        return "문법 오류"

    if "importerror" in lowered or "modulenotfounderror" in lowered or "cannot import" in lowered:
        return "import / 모듈 연결 오류"

    if "nameerror" in lowered or "not defined" in lowered:
        return "변수 또는 함수 이름 오류"

    if "attributeerror" in lowered or "has no attribute" in lowered:
        return "객체 속성 / 메서드 오류"

    if "typeerror" in lowered:
        return "자료형 또는 함수 호출 방식 오류"

    if "filenotfounderror" in lowered or "no such file" in lowered:
        return "파일 경로 오류"

    if "unicode" in lowered or "decode" in lowered or "utf-8" in lowered:
        return "인코딩 오류"

    if "404" in lowered or "500" in lowered or "http" in lowered:
        return "API / 서버 응답 오류"

    if "uvicorn" in lowered or "fastapi" in lowered:
        return "FastAPI 서버 실행 오류"

    if "button" in lowered or "onclick" in lowered or "addeventlistener" in lowered:
        return "프론트엔드 이벤트 연결 오류"

    if "git" in lowered:
        return "Git 작업 오류"

    return "일반 코드 문제"


def _extract_file_hints(user_input: str) -> list[str]:
    hints = []

    candidates = [
        "main.py",
        "config.py",
        "core/command_parser.py",
        "core/prompt_builder.py",
        "core/ai_client.py",
        "providers/mock_provider.py",
        "providers/gemini_provider.py",
        "providers/openai_provider.py",
        "static/index.html",
        "static/style.css",
        "static/app.js",
        ".env",
        "requirements.txt",
    ]

    lowered = user_input.lower()

    for candidate in candidates:
        if candidate.lower() in lowered:
            hints.append(candidate)

    return hints


def _extract_line_hints(user_input: str) -> list[str]:
    hints = []

    for line in user_input.splitlines():
        lowered = line.lower()

        if "line" in lowered or "줄" in lowered or "file" in lowered or "파일" in lowered:
            hints.append(line.strip())

    return hints[:5]


def _make_code_cause_candidates(error_type: str, user_input: str) -> list[str]:
    lowered = user_input.lower()

    if "mock response" in lowered and "code" in lowered:
        return [
            "/crenoba code가 Code Agent가 아니라 General Agent로 라우팅되고 있을 수 있습니다.",
            "prompt_builder에서 CRENOBA CODE AGENT 문자열이 생성되지 않았을 수 있습니다.",
            "mock_provider의 generate_response에서 CRENOBA CODE AGENT 분기 조건이 맞지 않을 수 있습니다.",
        ]

    if error_type == "문법 오류":
        return [
            "괄호, 따옴표, 콜론, 들여쓰기 중 하나가 깨졌을 가능성이 큽니다.",
            "PowerShell 명령어 안에서 줄바꿈이나 따옴표가 Python 문자열을 깨뜨렸을 수 있습니다.",
            "복사한 코드 일부가 누락되었을 가능성이 있습니다.",
        ]

    if error_type == "import / 모듈 연결 오류":
        return [
            "import하려는 함수 또는 클래스 이름이 실제 파일에 존재하지 않을 수 있습니다.",
            "파일명은 맞지만 함수명이 다르거나 아직 정의되지 않았을 수 있습니다.",
            "현재 실행 위치가 프로젝트 루트가 아닐 수 있습니다.",
        ]

    if error_type == "변수 또는 함수 이름 오류":
        return [
            "변수명 또는 함수명의 대소문자가 일치하지 않을 가능성이 큽니다.",
            "정의되기 전에 함수를 호출했을 수 있습니다.",
            "이전 버전 이름을 새 코드에서 그대로 사용했을 수 있습니다.",
        ]

    if error_type == "객체 속성 / 메서드 오류":
        return [
            "객체에 generate, call, run 같은 메서드가 없을 수 있습니다.",
            "provider 구조가 함수형인지 클래스형인지 통일되지 않았을 수 있습니다.",
            "어댑터가 실제 provider 객체를 제대로 감싸지 못했을 수 있습니다.",
        ]

    if error_type == "인코딩 오류":
        return [
            ".env 또는 코드 파일이 UTF-8이 아닌 형식으로 저장되었을 수 있습니다.",
            "PowerShell copy 명령으로 생성한 파일이 UTF-16으로 저장되었을 수 있습니다.",
            "python-dotenv가 UTF-8로 읽는 과정에서 실패했을 수 있습니다.",
        ]

    if error_type == "프론트엔드 이벤트 연결 오류":
        return [
            "HTML의 id와 app.js의 getElementById 이름이 일치하지 않을 수 있습니다.",
            "script 경로가 잘못되어 app.js가 로드되지 않았을 수 있습니다.",
            "브라우저 캐시 때문에 이전 JS 파일이 실행되고 있을 수 있습니다.",
        ]

    if error_type == "Git 작업 오류":
        return [
            "Git 사용자 이름과 이메일이 설정되지 않았을 수 있습니다.",
            "commit 전에 git add가 되지 않았을 수 있습니다.",
            "원격 저장소와 로컬 브랜치 상태가 달라 push가 거절되었을 수 있습니다.",
        ]

    return [
        "에러 로그의 마지막 줄을 기준으로 원인을 확인해야 합니다.",
        "수정한 파일과 실제 실행 중인 파일이 다를 수 있습니다.",
        "서버 재시작 또는 브라우저 강력 새로고침이 누락되었을 수 있습니다.",
    ]


def _make_code_solution_steps(error_type: str) -> list[str]:
    if error_type == "import / 모듈 연결 오류":
        return [
            "에러 메시지에서 import 실패한 함수명 또는 클래스명을 확인한다.",
            "해당 함수가 실제 파일에 정의되어 있는지 확인한다.",
            "main.py 또는 ai_client.py에서 import하는 이름과 실제 함수명을 맞춘다.",
            "서버를 재시작해서 import 에러가 사라졌는지 확인한다.",
        ]

    if error_type == "인코딩 오류":
        return [
            ".env 파일을 UTF-8로 다시 생성한다.",
            "비밀키가 필요한 경우 직접 다시 입력한다.",
            "서버를 재실행해서 dotenv 로딩이 성공하는지 확인한다.",
        ]

    if error_type == "프론트엔드 이벤트 연결 오류":
        return [
            "static/index.html의 버튼 id를 확인한다.",
            "static/app.js의 getElementById 값과 비교한다.",
            "script src 경로가 /app.js인지 확인한다.",
            "브라우저에서 Ctrl + Shift + R로 강력 새로고침한다.",
        ]

    if error_type == "Git 작업 오류":
        return [
            "git status로 현재 staged / unstaged 상태를 확인한다.",
            "user.name과 user.email 설정 여부를 확인한다.",
            "git add, commit, push 순서로 다시 진행한다.",
        ]

    return [
        "에러 로그의 마지막 줄을 먼저 확인한다.",
        "에러가 발생한 파일과 줄 번호를 찾는다.",
        "최근 수정한 파일부터 되돌아보며 원인을 좁힌다.",
        "수정 후 같은 명령어로 다시 실행한다.",
    ]


def _mock_code_response(prompt: str) -> str:
    user_input = _extract_user_input(prompt)
    error_type = _detect_error_type(user_input)
    file_hints = _extract_file_hints(user_input)
    line_hints = _extract_line_hints(user_input)
    cause_candidates = _make_code_cause_candidates(error_type, user_input)
    solution_steps = _make_code_solution_steps(error_type)

    if file_hints:
        file_text = "\n".join(f"- {file}" for file in file_hints)
    else:
        file_text = "- 아직 특정 파일이 감지되지 않았습니다. 에러 로그의 파일명 또는 수정한 파일명을 함께 넣으면 더 정확해집니다."

    if line_hints:
        line_text = "\n".join(f"- {line}" for line in line_hints)
    else:
        line_text = "- 아직 줄 번호 정보가 감지되지 않았습니다."

    return f"""
# CRENOBA Code Agent v0.8

입력 내용:
{user_input}

---

## 1. 문제 요약

현재 입력은 **{error_type}** 유형으로 판단됩니다.

Code Agent 기준으로 보면, 먼저 에러 로그의 마지막 줄과 최근 수정한 파일을 기준으로 원인을 좁혀야 합니다.

---

## 2. 에러 위치 / 의심 위치

감지된 파일 후보:

{file_text}

감지된 줄 번호 / 로그 힌트:

{line_text}

---

## 3. 원인 후보

{_format_bullet_list(cause_candidates)}

---

## 4. 해결 단계

{_format_bullet_list(solution_steps)}

---

## 5. 수정 코드

현재 mock provider 단계에서는 실제 코드를 자동 수정하지는 않습니다.

다만 다음 방식으로 수정하는 것이 좋습니다.

1. 에러가 난 파일을 연다.
2. 에러 메시지에 나온 함수명 / 변수명 / import 이름을 확인한다.
3. 실제 파일에 존재하는 이름과 호출하는 이름을 일치시킨다.
4. 수정 후 서버를 재실행한다.

코드 수정이 필요한 경우에는 해당 파일 전체 코드를 입력하면, CRENOBA Code Agent가 전체 파일 기준으로 수정안을 만들도록 설계할 수 있습니다.

---

## 6. 테스트 방법

FastAPI 서버 기준 테스트:

uvicorn main:app --reload

브라우저 UI 테스트:

http://127.0.0.1:8000
Ctrl + Shift + R

명령어 라우팅 테스트:

python -c "from core.prompt_builder import build_prompt; print(build_prompt('/crenoba code' + chr(10) + 'test')[:80])"

정상 기준:

# CRENOBA CODE AGENT v0.8

---

## 7. Git 체크리스트

수정이 끝나면 아래 순서로 GitHub에 올립니다.

git status
git add .
git commit -m "Improve code agent debugging response"
git push origin main
git status

마지막 git status에서 아래처럼 나오면 완료입니다.

nothing to commit, working tree clean
""".strip()


# ============================================================
# 기타 Agent 응답
# ============================================================

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
CRENOBA v0.8

## 2. 완료된 작업
- Core Agent 기본 구조
- mock provider 연결
- Web UI 연결
- Task Agent v0.7.4 고도화 완료
- Code Agent v0.8 고도화 진행

## 3. 중요한 결정
- CRENOBA는 브랜드형 챗봇이 아니라 목적별 업무 보조 Agent 시스템이다.
- /crenoba 명령어로 Agent를 실행한다.
- /gpt 명령어는 ChatGPT 작업 정리와 인수인계에 사용한다.

## 4. 현재 문제
현재 mock provider 기반으로 Agent 응답 구조를 테스트 중입니다.

## 5. 다음 작업
- Code Agent 실제 코드 수정 응답 강화
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
Agent별 고도화는 v0.8부터 Code Agent 중심으로 진행합니다.
""".strip()


# ============================================================
# Provider 진입점
# ============================================================

def generate_response(prompt: str) -> str:
    """
    main.py 또는 ai_client.py에서 호출하는 mock provider 진입점.
    """
    if not prompt:
        return _mock_default_response("")

    upper_prompt = prompt.upper()

    if "CRENOBA TASK AGENT" in upper_prompt:
        return _mock_task_response(prompt)

    if "CRENOBA STUDY AGENT" in upper_prompt:
        return _mock_study_response(prompt)

    if "CRENOBA CODE AGENT" in upper_prompt:
        return _mock_code_response(prompt)

    if "CRENOBA REPORT AGENT" in upper_prompt:
        return _mock_report_response(prompt)

    if "CRENOBA PROJECT AGENT" in upper_prompt:
        return _mock_project_response(prompt)

    if "CRENOBA APOLLO AGENT" in upper_prompt:
        return _mock_apollo_response(prompt)

    if "CRENOBA RELAY AGENT" in upper_prompt:
        return _mock_relay_response(prompt)

    return _mock_default_response(prompt)


class MockProvider:
    """
    ai_client.py에서 class 방식으로 호출할 수 있게 하는 Mock Provider.
    """

    def generate(self, prompt: str) -> str:
        return generate_response(prompt)

    def call(self, prompt: str) -> str:
        return generate_response(prompt)

    def run(self, prompt: str) -> str:
        return generate_response(prompt)