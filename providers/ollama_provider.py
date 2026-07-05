import os
import requests


class OllamaProvider:
    """
    CRENOBA Ollama Local Provider
    v0.9.5.2 Speed Hotfix
    - Task/Study/Code 응답 속도 개선
    - 프롬프트 최소화
    - num_predict 축소
    - qwen3 thinking 문제 방지: think=False
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

        system_prompt = self._build_system_prompt(agent)
        user_prompt = self._build_user_prompt(prompt, agent)

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
            "think": False,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": self._get_temperature(agent),
                "num_predict": self._get_num_predict(agent),
                "num_ctx": 1536,
                "top_p": 0.85,
                "repeat_penalty": 1.08,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=75)

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
                "1. 같은 요청을 한 번 더 실행해 모델이 메모리에 올라와 있는지 확인\n"
                "2. qwen3:14b 대신 더 작은 모델을 Agent별로 분리\n"
                "3. Code Agent는 qwen2.5-coder:7b-instruct 사용 검토\n"
                "4. Ollama 서버 재시작"
            )

        except Exception as e:
            return f"[CRENOBA Ollama Unknown Error]\n{str(e)}"

    def _build_user_prompt(self, prompt: str, agent: str) -> str:
        cleaned_prompt = self._strip_command_line(prompt)

        return f"""
요청:
{cleaned_prompt}

규칙:
- 한국어
- 최종 답변만
- 짧고 실행 가능하게
- 지정된 형식만 사용
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

    def _build_system_prompt(self, agent: str) -> str:
        common = """
너는 CRENOBA Agent다.
한국어로만 답한다.
생각 과정은 출력하지 않는다.
답변은 짧고 실용적으로 작성한다.
코드 수정 요청은 관련 파일 전체 코드로 제공한다.
""".strip()

        agent_prompts = {
            "task": """
Task 형식:
1. 핵심 목표
2. 반드시 할 일
3. 여유 시 할 일
4. 실행 순서
5. 다음 행동 1개

각 항목은 짧게 작성한다.
실제 소요시간은 추측하지 않는다.
""".strip(),

            "study": """
Study 형식:
1. 한 줄 요약
2. 쉬운 설명
3. 핵심 원리
4. 예시
5. 주의점

중학생도 이해할 정도로 쉽게 쓴다.
""".strip(),

            "code": """
Code 형식:
1. 문제 요약
2. 원인
3. 코드
4. 테스트 방법

실행 가능한 코드만 간결하게 제공한다.
수정 요청이면 관련 파일 전체 코드를 제공한다.
""".strip(),

            "report": """
Report 형식:
1. 제목
2. 핵심 요약
3. 본문
4. 정리 문장

문서는 깔끔하고 전문적으로 작성한다.
""".strip(),

            "project": """
Project 형식:
1. 현재 상태
2. 완료 작업
3. 남은 작업
4. 다음 우선순위
5. Git 체크리스트
""".strip(),

            "apollo": """
Apollo 형식:
1. 상황 요약
2. 핵심 원리
3. 구현/계산 방법
4. 테스트
5. 주의점

OpenCV, ROS2, Arduino, 모터 제어 관점으로 답한다.
""".strip(),

            "relay": """
Relay 형식:
1. 프로젝트 현재 상태
2. 버전별 기록
3. 파일 구조
4. 중요 결정
5. 다음 작업
6. Git 절차

새 채팅 인수인계 문서처럼 작성한다.
""".strip(),

            "general": """
요청에 맞춰 간결하고 실용적으로 답한다.
""".strip(),
        }

        return common + "\n\n" + agent_prompts.get(agent, agent_prompts["general"])

    def _get_temperature(self, agent: str) -> float:
        temperatures = {
            "code": 0.12,
            "task": 0.16,
            "study": 0.18,
            "report": 0.22,
            "project": 0.16,
            "apollo": 0.14,
            "relay": 0.18,
            "general": 0.18,
        }

        return temperatures.get(agent, 0.18)

    def _get_num_predict(self, agent: str) -> int:
        num_predict_map = {
            "task": 150,
            "study": 190,
            "code": 260,
            "report": 300,
            "project": 230,
            "apollo": 300,
            "relay": 520,
            "general": 180,
        }

        return num_predict_map.get(agent, 180)

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
            "1. payload 최상위에 think=False가 적용되어 있는지 확인하세요.\n"
            "2. Ollama 버전이 thinking 제어를 지원하는지 확인하세요.\n"
            "3. 계속 반복되면 non-thinking 계열 모델 사용을 추천합니다."
        )

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


def generate_response(prompt: str) -> str:
    return OllamaProvider().generate(prompt)