import os
import requests


class OllamaProvider:
    """
    CRENOBA Ollama Local Provider
    v0.9.4 Hotfix 2
    - qwen3 thinking field 문제 해결
    - top-level think=False 적용
    - content empty debug 유지
    - 응답 속도 개선
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.default_model = os.getenv("OLLAMA_MODEL", "qwen3:14b")

    def generate(
        self,
        prompt: str,
        model_override: str | None = None,
        agent: str = "general",
        mode: str = "general",
    ) -> str:
        model = model_override or self.default_model
        url = f"{self.base_url}/api/chat"

        system_prompt = self._build_system_prompt(agent, mode)

        user_prompt = f"""
아래 요청에 대해 최종 답변만 작성해.
생각 과정은 출력하지 마.
답변이 길 필요 없으면 짧고 명확하게 답해.

사용자 요청:
{prompt}
""".strip()

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            # 중요:
            # qwen3 계열이 content 대신 thinking에 토큰을 전부 쓰는 문제 방지
            "think": False,

            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": 0.2,
                "num_predict": 220,
                "num_ctx": 2048,
                "top_p": 0.9,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=120)

            if response.status_code != 200:
                return (
                    "[CRENOBA Ollama Error]\n"
                    f"Status Code: {response.status_code}\n"
                    f"Response: {response.text}"
                )

            data = response.json()
            message = data.get("message", {})
            content = message.get("content", "")

            cleaned = self._clean_output(content)

            if cleaned:
                return cleaned

            return self._empty_response_debug(data, model, agent, mode)

        except requests.exceptions.ConnectionError:
            return (
                "[CRENOBA Ollama Connection Error]\n"
                "Ollama 서버에 연결할 수 없습니다.\n\n"
                "확인 명령:\n"
                "Invoke-RestMethod http://localhost:11434/api/tags"
            )

        except requests.exceptions.Timeout:
            return (
                "[CRENOBA Ollama Timeout]\n"
                "로컬 모델 응답 시간이 너무 오래 걸렸습니다.\n\n"
                "해결 방법:\n"
                "1. num_predict 값을 더 줄이기\n"
                "2. qwen3:14b 대신 더 작은 모델 사용\n"
                "3. Ollama 서버 재시작\n"
            )

        except Exception as e:
            return f"[CRENOBA Ollama Unknown Error]\n{str(e)}"

    def _build_system_prompt(self, agent: str, mode: str) -> str:
        base = """
너는 CRENOBA 로컬 AI Agent다.
항상 한국어로 답한다.
생각 과정은 출력하지 않는다.
최종 답변만 출력한다.
사용자의 요청을 확대해석하지 않는다.
짧게 답하라는 요청이 있으면 1~3문장으로 답한다.
코드 수정이 필요하면 관련 파일 전체 코드를 제공한다.
""".strip()

        agent_prompts = {
            "code": """
현재 Agent는 Code Agent다.
코딩, 디버깅, 에러 분석, 파일 수정, 테스트 방법 안내를 우선한다.
답변 구조는 문제 요약, 원인, 수정 코드, 테스트 방법 순서로 작성한다.
""".strip(),

            "task": """
현재 Agent는 Task Agent다.
할 일을 우선순위, 긴급도, 예상 시간, 실행 순서로 정리한다.
바로 실행 가능한 다음 행동 1개를 반드시 제시한다.
""".strip(),

            "study": """
현재 Agent는 Study Agent다.
개념을 쉽게 설명하고, 필요한 경우 공식과 예시를 함께 제공한다.
사용자가 이해하기 쉽게 단계별로 설명한다.
""".strip(),

            "report": """
현재 Agent는 Report Agent다.
보고서, 문서, 발표 자료에 넣기 좋은 문장으로 정리한다.
문장은 깔끔하고 전문적으로 작성한다.
""".strip(),

            "project": """
현재 Agent는 Project Agent다.
프로젝트 진행 상황, 다음 작업, 위험 요소, 체크리스트를 중심으로 정리한다.
""".strip(),

            "apollo": """
현재 Agent는 Apollo Agent다.
자율주행, OpenCV, Arduino, 모터 제어, 공학 계산 관련 도움을 우선한다.
실험과 실제 구현 관점에서 설명한다.
""".strip(),

            "relay": """
현재 Agent는 Relay Agent다.
새 채팅으로 인수인계할 수 있도록 현재 상태, 버전, 결정 사항, 다음 작업을 문서화한다.
""".strip(),
        }

        return base + "\n\n" + agent_prompts.get(agent, "현재 Agent는 General Agent다.")

    def _clean_output(self, text: str) -> str:
        if not text:
            return ""

        cleaned = text.strip()

        if "</think>" in cleaned:
            cleaned = cleaned.split("</think>", 1)[1].strip()

        cleaned = cleaned.replace("<think>", "").replace("</think>", "").strip()

        return cleaned

    def _empty_response_debug(self, data: dict, model: str, agent: str, mode: str) -> str:
        message = data.get("message", {})
        done_reason = data.get("done_reason", "unknown")
        total_duration = data.get("total_duration", "unknown")
        eval_count = data.get("eval_count", "unknown")

        thinking = message.get("thinking", "")
        thinking_preview = thinking[:300] if thinking else ""

        return (
            "[CRENOBA Ollama Empty Response]\n"
            "Ollama 호출은 성공했지만 최종 답변 content가 비어 있습니다.\n\n"
            f"Model: {model}\n"
            f"Agent: {agent}\n"
            f"Mode: {mode}\n"
            f"Done Reason: {done_reason}\n"
            f"Total Duration: {total_duration}\n"
            f"Eval Count: {eval_count}\n"
            f"Message Keys: {list(message.keys())}\n\n"
            f"Thinking Preview: {thinking_preview}\n\n"
            "해결 방향:\n"
            "1. payload 최상위에 think=False를 적용했습니다.\n"
            "2. 그래도 비어 있으면 Ollama 버전 또는 qwen3 모델 동작 문제일 수 있습니다.\n"
            "3. 계속 반복되면 qwen2.5-coder:7b-instruct 같은 non-thinking 계열 모델 사용을 추천합니다."
        )

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


def generate_response(prompt: str) -> str:
    return OllamaProvider().generate(prompt)