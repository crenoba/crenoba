const promptInput = document.getElementById("promptInput");
const outputBox = document.getElementById("outputBox");

const runBtn = document.getElementById("runBtn");
const clearInputBtn = document.getElementById("clearInputBtn");
const copyOutputBtn = document.getElementById("copyOutputBtn");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");

const providerStatus = document.getElementById("providerStatus");
const modeStatus = document.getElementById("modeStatus");
const agentStatus = document.getElementById("agentStatus");
const readyStatus = document.getElementById("readyStatus");
const commandStatus = document.getElementById("commandStatus");
const responseAgentStatus = document.getElementById("responseAgentStatus");
const responseProviderStatus = document.getElementById("responseProviderStatus");
const historyList = document.getElementById("historyList");

const HISTORY_KEY = "crenoba_command_history_v07";

const commandExamples = {
  "/crenoba task": `/crenoba task
오늘 해야 할 일:
- CRENOBA v0.7 Task Agent 고도화
- 웹 UI v0.7 적용
- mock provider 테스트
- GitHub에 작업 내용 올리기`,

  "/crenoba study": `/crenoba study
공부할 내용:
- 핵심 개념 정리
- 예제 풀이
- 헷갈리는 부분 질문 만들기`,

  "/crenoba code": `/crenoba code
코드 문제:
- 에러 메시지 붙여넣기
- 문제가 생긴 파일 설명
- 원하는 동작 설명`,

  "/crenoba report": `/crenoba report
보고서 주제:
- 목적
- 들어가야 할 내용
- 발표 또는 제출 형식`,

  "/crenoba project": `/crenoba project
프로젝트 상태:
- 완료한 것
- 진행 중인 것
- 막힌 것
- 다음 목표`,

  "/crenoba apollo": `/crenoba apollo
Apollo 작업:
- OpenCV 차선 인식
- Arduino 모터 제어
- INPOS / Encoder / 브레이크 테스트`,

  "/crenoba relay": `/crenoba relay
현재 작업 상태를 다음 채팅에서도 이어갈 수 있게 정리해줘.`
};

function detectCommand(text) {
  const firstLine = text.trim().split("\n")[0].trim();

  if (firstLine.startsWith("/crenoba task")) return "task";
  if (firstLine.startsWith("/crenoba study")) return "study";
  if (firstLine.startsWith("/crenoba code")) return "code";
  if (firstLine.startsWith("/crenoba report")) return "report";
  if (firstLine.startsWith("/crenoba project")) return "project";
  if (firstLine.startsWith("/crenoba apollo")) return "apollo";
  if (firstLine.startsWith("/crenoba relay")) return "relay";

  return "general";
}

function updateStatus(mode, provider = "mock") {
  const agentName = mode === "general" ? "-" : `${mode} agent`;

  providerStatus.textContent = provider;
  modeStatus.textContent = mode;
  agentStatus.textContent = agentName;

  commandStatus.textContent = mode;
  responseAgentStatus.textContent = agentName;
  responseProviderStatus.textContent = provider;
}

function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
  } catch {
    return [];
  }
}

function saveHistory(prompt) {
  const history = getHistory();
  const trimmed = prompt.trim();

  if (!trimmed) return;

  const nextHistory = [
    trimmed,
    ...history.filter((item) => item !== trimmed)
  ].slice(0, 8);

  localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
  renderHistory();
}

function renderHistory() {
  const history = getHistory();
  historyList.innerHTML = "";

  if (history.length === 0) {
    historyList.innerHTML = `<p class="empty">아직 실행 기록이 없습니다.</p>`;
    return;
  }

  history.forEach((item) => {
    const div = document.createElement("div");
    div.className = "history-item";
    div.textContent = item.length > 120 ? `${item.slice(0, 120)}...` : item;
    div.addEventListener("click", () => {
      promptInput.value = item;
      updateStatus(detectCommand(item));
    });
    historyList.appendChild(div);
  });
}

async function runAgent() {
  const prompt = promptInput.value.trim();

  if (!prompt) {
    outputBox.textContent = "입력 내용이 없습니다.";
    return;
  }

  const mode = detectCommand(prompt);
  updateStatus(mode);

  readyStatus.textContent = "실행 중...";
  outputBox.textContent = "CRENOBA Agent 실행 중...";

  try {
    const response = await fetch("/relay", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ prompt })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    const provider = data.provider || "mock";
    const resultMode = data.mode || mode;
    const output = data.output || JSON.stringify(data, null, 2);

    updateStatus(resultMode, provider);

    readyStatus.textContent = "완료";
    outputBox.textContent = output;

    saveHistory(prompt);
  } catch (error) {
    readyStatus.textContent = "오류";
    outputBox.textContent = `에러가 발생했습니다.\n\n${error.message}`;
  }
}

runBtn.addEventListener("click", runAgent);

clearInputBtn.addEventListener("click", () => {
  promptInput.value = "";
  promptInput.focus();
});

copyOutputBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(outputBox.textContent);
    copyOutputBtn.textContent = "Copied";
    setTimeout(() => {
      copyOutputBtn.textContent = "Copy Output";
    }, 900);
  } catch {
    outputBox.textContent += "\n\n복사에 실패했습니다.";
  }
});

clearHistoryBtn.addEventListener("click", () => {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
});

document.querySelectorAll("[data-command]").forEach((button) => {
  button.addEventListener("click", () => {
    const command = button.dataset.command;
    promptInput.value = commandExamples[command] || command;
    updateStatus(detectCommand(promptInput.value));
    promptInput.focus();
  });
});

promptInput.addEventListener("input", () => {
  updateStatus(detectCommand(promptInput.value));
});

renderHistory();
updateStatus(detectCommand(promptInput.value));