import json
import os
import urllib.error
import urllib.request


class OllamaProvider:
    """
    CRENOBA Ollama Provider v0.9.6

    핵심 변경:
    - Agent별 model을 AIClient에서 전달받음
    - qwen3 계열 Empty Response 방지를 위해 think=False 유지
    - Agent별 num_predict 최적화
    - Code/Apollo는 qwen2.5-coder:7b-instruct 사용 가능
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        self.default_model = os.getenv("OLLAMA_MODEL", "qwen3:14b").strip()
        self.timeout = 90

    def generate_response(
        self,
        prompt: str,
        mode: str | None = None,
        agent: str | None = None,
        model: str | None = None,
    ) -> str:
        selected_agent = self._normalize_agent(agent or mode)
        selected_model = model or self._get_agent_model(selected_agent)

        system_prompt = self._build_system_prompt(selected_agent)

        payload = {
            "model": selected_model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
            "keep_alive": "30m",

            # qwen3 thinking 문제 방지
            # content가 비고 thinking에만 답변이 들어가는 문제를 막기 위함
            "think": False,

            "options": {
                "temperature": self._get_temperature(selected_agent),
                "num_predict": self._get_num_predict(selected_agent),
                "num_ctx": 1536,
                "top_p": 0.85,
                "repeat_penalty": 1.08,
            },
        }

        try:
            response_data = self._post_chat(payload)
            return self._extract_content(
                response_data=response_data,
                model=selected_model,
                agent=selected_agent,
                mode=mode,
            )

        except urllib.error.URLError as e:
            return (
                "[CRENOBA Ollama Connection Error]\n\n"
                "Ollama 서버에 연결하지 못했습니다.\n\n"
                f"URL: {self.base_url}\n"
                f"Model: {selected_model}\n"
                f"Agent: {selected_agent}\n\n"
                "확인할 것:\n"
                "1. Ollama가 실행 중인지 확인\n"
                "2. PowerShell에서 `ollama list` 확인\n"
                "3. `ollama serve` 또는 Ollama 앱 실행 확인\n\n"
                f"Error: {str(e)}"
            )

        except Exception as e:
            return (
                "[CRENOBA Ollama Error]\n\n"
                f"Model: {selected_model}\n"
                f"Agent: {selected_agent}\n"
                f"Error: {str(e)}"
            )

    def _post_chat(self, payload: dict) -> dict:
        url = f"{self.base_url}/api/chat"

        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")

        return json.loads(raw)

    def _extract_content(
        self,
        response_data: dict,
        model: str,
        agent: str,
        mode: str | None,
    ) -> str:
        message = response_data.get("message", {})
        content = message.get("content", "")

        if isinstance(content, str):
            content = content.strip()

        if content:
            return content

        thinking = message.get("thinking", "")

        if isinstance(thinking, str) and thinking.strip():
            return (
                "[CRENOBA Ollama Empty Response]\n\n"
                "Ollama 호출은 성공했지만 최종 답변 content가 비어 있습니다.\n"
                "thinking 필드에만 내용이 들어왔습니다.\n\n"
                f"Model: {model}\n"
                f"Agent: {agent}\n"
                f"Mode: {mode}\n"
                f"Done Reason: {response_data.get('done_reason')}\n"
                f"Eval Count: {response_data.get('eval_count')}\n"
                f"Message Keys: {list(message.keys())}\n\n"
                "해결 후보:\n"
                "1. qwen3 모델이면 think=False 적용 여부 확인\n"
                "2. qwen2.5-coder 같은 non-thinking 모델 사용\n"
                "3. num_predict 값을 조금 늘리기\n"
            )

        return (
            "[CRENOBA Ollama Empty Response]\n\n"
            "Ollama 호출은 성공했지만 응답 내용이 비어 있습니다.\n\n"
            f"Model: {model}\n"
            f"Agent: {agent}\n"
            f"Mode: {mode}\n"
            f"Done Reason: {response_data.get('done_reason')}\n"
            f"Eval Count: {response_data.get('eval_count')}\n"
            f"Message Keys: {list(message.keys())}"
        )

    def _normalize_agent(self, agent: str | None) -> str:
        if not agent:
            return "general"

        cleaned = str(agent).strip().lower()

        allowed_agents = {
            "task",
            "study",
            "code",
            "report",
            "project",
            "apollo",
            "relay",
            "general",
        }

        if cleaned in allowed_agents:
            return cleaned

        return "general"

    def _get_agent_model(self, agent: str) -> str:
        env_key = f"{agent.upper()}_OLLAMA_MODEL"
        return os.getenv(env_key, self.default_model).strip()

    def _get_temperature(self, agent: str) -> float:
        temperature_map = {
            "task": 0.2,
            "study": 0.25,
            "code": 0.1,
            "report": 0.35,
            "project": 0.2,
            "apollo": 0.1,
            "relay": 0.2,
            "general": 0.3,
        }

        return temperature_map.get(agent, 0.3)

    def _get_num_predict(self, agent: str) -> int:
        num_predict_map = {
            "task": 150,
            "study": 260,
            "code": 280,
            "report": 300,
            "project": 230,
            "apollo": 320,
            "relay": 520,
            "general": 180,
        }

        return num_predict_map.get(agent, 180)

    def _build_system_prompt(self, agent: str) -> str:
        common = (
            "너는 CRENOBA의 목적별 AI Agent다. "
            "한국어로 답한다. "
            "불필요한 설명을 줄이고 바로 실행 가능한 답을 준다. "
            "모르면 추측하지 말고 확인이 필요하다고 말한다."
        )

        prompts = {
            "task": (
                f"{common}\n"
                "역할: Task Agent.\n"
                "사용자의 할 일을 우선순위와 실행 순서로 정리한다.\n"
                "형식:\n"
                "1. 핵심 목표\n"
                "2. 먼저 할 일\n"
                "3. 다음 할 일\n"
                "4. 미뤄도 되는 일\n"
                "5. 바로 시작할 행동 1개"
            ),
            "study": (
                f"{common}\n"
                "역할: Study Agent.\n"
                "개념을 쉽게 설명한다.\n"
                "형식:\n"
                "1. 한 줄 요약\n"
                "2. 쉬운 설명\n"
                "3. 핵심 원리\n"
                "4. 예시\n"
                "5. 헷갈리는 부분"
            ),
            "code": (
                f"{common}\n"
                "역할: Code Agent.\n"
                "코딩, 디버깅, 구조 개선을 돕는다.\n"
                "사용자가 코드 수정을 요청하면 가능한 전체 파일 기준으로 제공한다.\n"
                "형식:\n"
                "1. 문제 요약\n"
                "2. 원인\n"
                "3. 수정 방향\n"
                "4. 수정 코드\n"
                "5. 테스트 방법"
            ),
            "report": (
                f"{common}\n"
                "역할: Report Agent.\n"
                "보고서, 정리문, 문서 초안을 작성한다.\n"
                "형식:\n"
                "1. 제목\n"
                "2. 핵심 요약\n"
                "3. 본문\n"
                "4. 정리 문장"
            ),
            "project": (
                f"{common}\n"
                "역할: Project Agent.\n"
                "프로젝트 상태, 남은 작업, 우선순위, 위험 요소를 정리한다.\n"
                "형식:\n"
                "1. 현재 상태\n"
                "2. 완료된 작업\n"
                "3. 남은 작업\n"
                "4. 다음 우선순위\n"
                "5. 위험 요소\n"
                "6. Git 체크리스트"
            ),
            "apollo": (
                f"{common}\n"
                "역할: Apollo Agent.\n"
                "자율주행, Arduino, 모터 제어, OpenCV, ROS2 관련 문제를 돕는다.\n"
                "형식:\n"
                "1. 문제 상황 요약\n"
                "2. 핵심 원리\n"
                "3. 구현 또는 계산 방법\n"
                "4. 테스트 방법\n"
                "5. 주의할 점"
            ),
            "relay": (
                f"{common}\n"
                "역할: Relay Agent.\n"
                "새 채팅으로 이어갈 수 있는 인수인계 문서를 만든다.\n"
                "형식:\n"
                "1. 프로젝트 현재 상태\n"
                "2. 완료된 버전별 기록\n"
                "3. 현재 파일 구조\n"
                "4. 중요한 결정 사항\n"
                "5. 다음 작업 방향\n"
                "6. Git 상태 및 업로드 절차"
            ),
            "general": (
                f"{common}\n"
                "역할: General Agent.\n"
                "사용자의 요청을 간결하고 실용적으로 처리한다."
            ),
        }

        return prompts.get(agent, prompts["general"])