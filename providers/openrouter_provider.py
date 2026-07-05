import os
import requests


class OpenRouterProvider:
    """
    CRENOBA OpenRouter Provider
    v0.9.5
    - Agent별 출력 품질 고도화
    - Agent별 max_tokens 조절
    - 명령어 라인 제거 후 실제 요청 중심 처리
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.default_model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(
        self,
        prompt: str,
        model_override: str | None = None,
        agent: str = "general",
        mode: str = "general",
    ) -> str:
        if not self.api_key:
            return (
                "[CRENOBA OpenRouter Error]\n"
                "OPENROUTER_API_KEY가 .env에 설정되어 있지 않습니다."
            )

        model = model_override or self.default_model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "CRENOBA",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": self._build_system_prompt(agent, mode),
                },
                {
                    "role": "user",
                    "content": self._build_user_prompt(prompt, agent),
                },
            ],
            "temperature": self._get_temperature(agent),
            "max_tokens": self._get_max_tokens(agent),
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=120,
            )

            if response.status_code != 200:
                return (
                    "[CRENOBA OpenRouter Error]\n"
                    f"Status Code: {response.status_code}\n"
                    f"Response: {response.text}"
                )

            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            return (
                "[CRENOBA OpenRouter Timeout]\n"
                "OpenRouter 응답 시간이 너무 오래 걸렸습니다."
            )

        except Exception as e:
            return f"[CRENOBA OpenRouter Unknown Error]\n{str(e)}"

    def _build_user_prompt(self, prompt: str, agent: str) -> str:
        cleaned_prompt = self._strip_command_line(prompt)

        return f"""
아래 사용자 요청을 처리해.

중요 규칙:
- 한국어로 답한다.
- 사용자가 원하는 결과물을 바로 쓸 수 있게 만든다.
- 불필요한 사족을 줄인다.

현재 Agent:
{agent}

사용자 요청:
{cleaned_prompt}
""".strip()

    def _strip_command_line(self, prompt: str) -> str:
        if not prompt:
            return ""

        lines = prompt.strip().splitlines()

        if not lines:
            return ""

        first_line = lines[0].strip()

        if first_line.startswith("/"):
            return "\n".join(lines[1:]).strip()

        return prompt.strip()

    def _build_system_prompt(self, agent: str, mode: str) -> str:
        base = """
너는 CRENOBA Agent System의 외부 AI Provider다.

공통 원칙:
- 항상 한국어로 답한다.
- 사용자의 요청을 실무적으로 처리한다.
- 결과물을 바로 사용할 수 있는 형태로 작성한다.
- 코드 수정이 필요한 경우 관련 파일 전체 코드를 제공한다.
""".strip()

        agent_prompts = {
            "task": """
현재 Agent는 Task Agent다.

출력 형식:
1. 오늘의 핵심 목표
2. 반드시 해야 할 일
3. 시간이 남으면 할 일
4. 미뤄도 되는 일
5. 추천 실행 순서
6. 바로 시작할 다음 행동 1개
""".strip(),

            "study": """
현재 Agent는 Study Agent다.

출력 형식:
1. 한 줄 요약
2. 쉬운 설명
3. 핵심 원리
4. 간단한 예시
5. 헷갈리기 쉬운 부분
""".strip(),

            "code": """
현재 Agent는 Code Agent다.

출력 형식:
1. 문제 요약
2. 원인
3. 수정 방향
4. 수정 코드
5. 테스트 방법

중요:
코드 수정이 필요한 경우 관련 파일 전체 코드를 제공한다.
""".strip(),

            "report": """
현재 Agent는 Report Agent다.

출력 형식:
1. 제목
2. 핵심 요약
3. 본문
4. 정리 문장
""".strip(),

            "project": """
현재 Agent는 Project Agent다.

출력 형식:
1. 현재 상태
2. 완료된 작업
3. 남은 작업
4. 다음 우선순위
5. 위험 요소
6. Git 체크리스트
""".strip(),

            "apollo": """
현재 Agent는 Apollo Agent다.

출력 형식:
1. 문제 상황 요약
2. 핵심 원리
3. 구현 또는 계산 방법
4. 테스트 방법
5. 주의할 점
""".strip(),

            "relay": """
현재 Agent는 Relay Agent다.

출력 형식:
1. 프로젝트 현재 상태
2. 완료된 버전별 기록
3. 현재 파일 구조
4. 중요한 결정 사항
5. 다음 작업 방향
6. Git 상태 및 업로드 절차
""".strip(),

            "general": """
현재 Agent는 General Agent다.
요청에 맞춰 간결하고 실용적으로 답한다.
""".strip(),
        }

        return base + "\n\n" + agent_prompts.get(agent, agent_prompts["general"])

    def _get_temperature(self, agent: str) -> float:
        temperatures = {
            "code": 0.15,
            "task": 0.25,
            "study": 0.25,
            "report": 0.3,
            "project": 0.2,
            "apollo": 0.18,
            "relay": 0.2,
            "general": 0.25,
        }

        return temperatures.get(agent, 0.25)

    def _get_max_tokens(self, agent: str) -> int:
        max_tokens_map = {
            "task": 700,
            "study": 800,
            "code": 1000,
            "report": 1100,
            "project": 900,
            "apollo": 1100,
            "relay": 1600,
            "general": 700,
        }

        return max_tokens_map.get(agent, 700)

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


def generate_response(prompt: str) -> str:
    return OpenRouterProvider().generate(prompt)