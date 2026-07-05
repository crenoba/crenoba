const messageInput = document.getElementById("messageInput");
const outputBox = document.getElementById("outputBox");

const statusBadge = document.getElementById("statusBadge");
const commandText = document.getElementById("commandText");
const agentText = document.getElementById("agentText");
const providerText = document.getElementById("providerText");
const modelText = document.getElementById("modelText");
const historyList = document.getElementById("historyList");

const providerCard = document.getElementById("providerCard");
const modeCard = document.getElementById("modeCard");
const agentCard = document.getElementById("agentCard");

const taskButton = document.getElementById("taskButton");
const studyButton = document.getElementById("studyButton");
const codeButton = document.getElementById("codeButton");
const reportButton = document.getElementById("reportButton");
const projectButton = document.getElementById("projectButton");
const apolloButton = document.getElementById("apolloButton");
const relayButton = document.getElementById("relayButton");

const runButton = document.getElementById("runButton");
const clearButton = document.getElementById("clearButton");
const clearHistoryButton = document.getElementById("clearHistoryButton");
const copyButton = document.getElementById("copyButton");

const HISTORY_KEY = "crenoba_command_history";

const examples = {
  task: `/crenoba task
오늘 해야 할 일:
- CRENOBA Agent 명령어 리팩토링
- 웹 UI 버튼 수정
- mock provider 테스트
- 다음 단계 정리`,

  study: `/crenoba study
열역학 포화액과 포화증기 개념을 과제에 쓸 수 있게 정리해줘.`,

  code: `/crenoba code
FastAPI와 JavaScript 웹 UI가 연결되는 구조를 설명하고, 버튼이 안 눌릴 때 확인할 점을 정리해줘.`,

  report: `/crenoba report
CRENOBA 업무 보조 AI Agent 시스템 설계 내용을 보고서 형식으로 정리해줘.`,

  project: `/crenoba project
CRENOBA를 올해 안에 업무 보조 AI Agent MVP로 만들고 싶어. 현재는 mock provider와 웹 UI까지 만들었어.`,

  apollo: `/crenoba apollo
OpenCV 차선 인식 파이프라인을 Apollo 프로젝트 기준으로 다시 정리해줘.`,

  relay: `/crenoba relay
현재 CRENOBA Core Agent v0.6을 만들고 있다. 목표는 브랜드형 챗봇이 아니라 업무 보조용 목적별 AI Agent 시스템이다.`
};

function setExample(type) {
  messageInput.value = examples[type] || examples.task;
  modeCard.textContent = type;
}

async function sendMessage() {
  const message = messageInput.value.trim();

  if (!message) {
    outputBox.textContent = "메시지를 입력하세요.";
    setStatus("Empty");
    return;
  }

  setStatus("Running...");
  outputBox.textContent = "Agent가 응답을 생성하는 중입니다...";

  resetMeta();

  try {
    const response = await fetch("/agent", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message: message })
    });

    const data = await response.json();

    commandText.textContent = data.command || "-";
    agentText.textContent = data.agent || "-";
    providerText.textContent = data.provider || "-";
    modelText.textContent = data.model || "-";

    providerCard.textContent = data.provider || "-";
    modeCard.textContent = data.command || "-";
    agentCard.textContent = data.agent || "-";

    if (data.error) {
      setStatus("Error");
      outputBox.textContent =
        typeof data.error === "string"
          ? data.error
          : JSON.stringify(data.error, null, 2);
      return;
    }

    setStatus("Done");
    outputBox.textContent = data.output || "응답이 비어 있습니다.";

    saveHistory({
      message: message,
      command: data.command || "-",
      agent: data.agent || "-",
      provider: data.provider || "-",
      model: data.model || "-",
      output: data.output || ""
    });

  } catch (error) {
    setStatus("Error");
    outputBox.textContent = `요청 중 오류가 발생했습니다.\n\n${error}`;
  }
}

async function copyOutput() {
  const text = outputBox.textContent;

  if (!text || text === "결과가 여기에 표시됩니다.") {
    setStatus("Nothing to copy");
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    setStatus("Copied");
  } catch (error) {
    setStatus("Copy failed");
    outputBox.textContent += `\n\n[Copy Error]\n${error}`;
  }
}

function clearAll() {
  messageInput.value = "";
  outputBox.textContent = "결과가 여기에 표시됩니다.";

  setStatus("Ready");
  resetMeta();

  providerCard.textContent = "mock";
  modeCard.textContent = "Ready";
  agentCard.textContent = "-";
}

function saveHistory(item) {
  const history = getHistory();

  const nextHistory = [
    {
      ...item,
      createdAt: new Date().toLocaleString()
    },
    ...history
  ].slice(0, 10);

  localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
  renderHistory();
}

function getHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (error) {
    return [];
  }
}

function renderHistory() {
  const history = getHistory();

  if (!history.length) {
    historyList.innerHTML = `<p class="empty-history">아직 실행 기록이 없습니다.</p>`;
    return;
  }

  historyList.innerHTML = history.map((item, index) => {
    const preview = item.message
      .replace(/\n/g, " ")
      .slice(0, 90);

    return `
      <div class="history-item" data-index="${index}">
        <p class="history-command">/crenoba ${escapeHtml(item.command)} · ${escapeHtml(item.agent)}</p>
        <p class="history-preview">${escapeHtml(preview)}</p>
      </div>
    `;
  }).join("");

  const items = document.querySelectorAll(".history-item");

  items.forEach((item) => {
    item.addEventListener("click", () => {
      const index = Number(item.dataset.index);
      loadHistory(index);
    });
  });
}

function loadHistory(index) {
  const history = getHistory();
  const item = history[index];

  if (!item) return;

  messageInput.value = item.message;
  outputBox.textContent = item.output || "저장된 응답이 없습니다.";

  commandText.textContent = item.command || "-";
  agentText.textContent = item.agent || "-";
  providerText.textContent = item.provider || "-";
  modelText.textContent = item.model || "history";

  providerCard.textContent = item.provider || "-";
  modeCard.textContent = item.command || "-";
  agentCard.textContent = item.agent || "-";

  setStatus("Loaded");
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
  setStatus("History cleared");
}

function resetMeta() {
  commandText.textContent = "-";
  agentText.textContent = "-";
  providerText.textContent = "-";
  modelText.textContent = "-";
}

function setStatus(text) {
  statusBadge.textContent = text;
  modeCard.textContent = text;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function bindEvents() {
  taskButton.addEventListener("click", () => setExample("task"));
  studyButton.addEventListener("click", () => setExample("study"));
  codeButton.addEventListener("click", () => setExample("code"));
  reportButton.addEventListener("click", () => setExample("report"));
  projectButton.addEventListener("click", () => setExample("project"));
  apolloButton.addEventListener("click", () => setExample("apollo"));
  relayButton.addEventListener("click", () => setExample("relay"));

  runButton.addEventListener("click", sendMessage);
  clearButton.addEventListener("click", clearAll);
  clearHistoryButton.addEventListener("click", clearHistory);
  copyButton.addEventListener("click", copyOutput);
}

bindEvents();
renderHistory();