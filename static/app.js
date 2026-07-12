const promptInput = document.getElementById("promptInput");
const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");
const copyBtn = document.getElementById("copyBtn");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const outputBox = document.getElementById("outputBox");
const historyList = document.getElementById("historyList");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

const approvalPanel = document.getElementById("approvalPanel");
const approvalSummary = document.getElementById("approvalSummary");
const approveBtn = document.getElementById("approveBtn");
const cancelApprovalBtn = document.getElementById("cancelApprovalBtn");

const modeValue = document.getElementById("modeValue");
const agentValue = document.getElementById("agentValue");
const providerValue = document.getElementById("providerValue");
const modelValue = document.getElementById("modelValue");
const timeValue = document.getElementById("timeValue");
const versionValue = document.getElementById("versionValue");

const HISTORY_KEY = "crenoba_command_history_v0102";
const LEGACY_HISTORY_KEYS = [
  "crenoba_command_history_v0101",
  "crenoba_command_history_v0952",
];
const APP_VERSION = "v0.10.2";

let currentPendingActionId = null;
let currentPendingPrompt = "";

function setStatus(type, text) {
  statusDot.className = `status-dot ${type}`;
  statusText.textContent = text;
}

function updateMetadata(data) {
  modeValue.textContent = data.mode || "general";
  agentValue.textContent = data.agent || "general";
  providerValue.textContent = data.provider || "unknown";
  modelValue.textContent = data.model || "unknown";
  timeValue.textContent = Number.isFinite(data.response_time_sec)
    ? `${data.response_time_sec}s`
    : "-";
  versionValue.textContent = data.version || APP_VERSION;
}

function isComputerCommand(prompt) {
  const firstLine = prompt.split("\n", 1)[0].trim().toLowerCase();
  return firstLine === "/crenoba computer" || firstLine === "/computer";
}

function showApproval(data, prompt) {
  currentPendingActionId = data.action_id;
  currentPendingPrompt = prompt;
  const tool = data.selected_tool || "computer action";
  const expiresAt = data.expires_at
    ? new Date(data.expires_at).toLocaleString("ko-KR")
    : "15분 이내";
  approvalSummary.textContent = `${tool} · ${expiresAt}까지 승인 가능`;
  approvalPanel.hidden = false;
  approveBtn.disabled = false;
  cancelApprovalBtn.disabled = false;
  setStatus("running", "Approval Required");
}

function hideApproval() {
  currentPendingActionId = null;
  currentPendingPrompt = "";
  approvalPanel.hidden = true;
  approveBtn.disabled = false;
  cancelApprovalBtn.disabled = false;
}

async function runAgent() {
  const prompt = promptInput.value.trim();

  if (!prompt) {
    outputBox.textContent = "명령어와 요청을 입력해주세요.";
    setStatus("error", "Empty Input");
    return;
  }

  if (currentPendingActionId) {
    outputBox.textContent = [
      "[CRENOBA Approval]",
      "현재 승인 대기 중인 작업이 있습니다.",
      "먼저 Approve & Execute 또는 Cancel을 선택해주세요.",
    ].join("\n");
    setStatus("running", "Approval Pending");
    return;
  }

  const computerMode = isComputerCommand(prompt);
  const endpoint = computerMode ? "/computer/chat" : "/relay";

  setStatus("running", computerMode ? "Running Computer" : "Running");
  runBtn.disabled = true;
  outputBox.textContent = computerMode
    ? "CRENOBA Computer Agent가 요청을 분석하고 안전한 실행 계획을 만드는 중입니다..."
    : "CRENOBA Agent가 응답을 생성하는 중입니다...";

  try {
    const payload = computerMode ? { prompt, cwd: "." } : { prompt };
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        detail = errorData.detail || detail;
      } catch {
        // Keep the HTTP status when the response is not JSON.
      }
      throw new Error(detail);
    }

    const data = await response.json();
    outputBox.textContent = data.output || JSON.stringify(data, null, 2);
    updateMetadata(data);
    saveHistory(prompt, data);
    renderHistory();

    if (data.requires_approval && data.action_id) {
      showApproval(data, prompt);
    } else {
      setStatus(data.success === false ? "error" : "done", data.success === false ? "Failed" : "Complete");
    }
  } catch (error) {
    outputBox.textContent = [
      "[CRENOBA UI Error]",
      "서버 요청 중 문제가 발생했습니다.",
      "",
      `Detail: ${error.message}`,
      "",
      "확인할 것:",
      "1. uvicorn 서버가 켜져 있는지 확인",
      "2. http://127.0.0.1:8000 으로 접속했는지 확인",
      `3. ${endpoint} API가 정상 작동하는지 확인`,
    ].join("\n");
    setStatus("error", "Error");
  } finally {
    runBtn.disabled = false;
  }
}

async function approvePendingAction() {
  if (!currentPendingActionId) {
    return;
  }

  const actionId = currentPendingActionId;
  const originalPrompt = currentPendingPrompt;
  approveBtn.disabled = true;
  cancelApprovalBtn.disabled = true;
  setStatus("running", "Executing Approved Action");
  outputBox.textContent = "승인된 작업을 실제 컴퓨터에서 실행하는 중입니다...";

  try {
    const response = await fetch("/computer/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: actionId }),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    outputBox.textContent = data.output || JSON.stringify(data, null, 2);
    updateMetadata(data);
    saveHistory(`[승인 실행] ${originalPrompt}`, data);
    renderHistory();
    hideApproval();
    setStatus(data.success ? "done" : "error", data.success ? "Executed" : "Execution Failed");
  } catch (error) {
    outputBox.textContent = `[CRENOBA Approval Error]\n${error.message}`;
    approveBtn.disabled = false;
    cancelApprovalBtn.disabled = false;
    setStatus("error", "Approval Error");
  }
}

async function cancelPendingAction(silent = false) {
  if (!currentPendingActionId) {
    return;
  }

  const actionId = currentPendingActionId;
  approveBtn.disabled = true;
  cancelApprovalBtn.disabled = true;

  try {
    const response = await fetch("/computer/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: actionId }),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    hideApproval();
    if (!silent) {
      outputBox.textContent = data.output || "작업을 취소했습니다.";
      updateMetadata(data);
      setStatus("idle", "Cancelled");
    }
  } catch (error) {
    approveBtn.disabled = false;
    cancelApprovalBtn.disabled = false;
    if (!silent) {
      outputBox.textContent = `[CRENOBA Approval Error]\n${error.message}`;
      setStatus("error", "Cancel Error");
    }
  }
}

async function clearInput() {
  await cancelPendingAction(true);
  promptInput.value = "";
  outputBox.textContent = "아직 실행된 명령이 없습니다.";
  modeValue.textContent = "general";
  agentValue.textContent = "general";
  providerValue.textContent = "waiting";
  modelValue.textContent = "waiting";
  timeValue.textContent = "-";
  versionValue.textContent = APP_VERSION;
  setStatus("idle", "Ready");
}

async function copyOutput() {
  const text = outputBox.textContent.trim();
  if (!text) {
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    setStatus("done", "Copied");
  } catch {
    setStatus("error", "Copy Failed");
  }
}

function insertCommand(command) {
  const current = promptInput.value.trim();

  if (!current) {
    promptInput.value = `${command}\n`;
  } else {
    const lines = current.split("\n");
    const firstLine = lines[0].trim();

    if (firstLine.startsWith("/")) {
      lines[0] = command;
      promptInput.value = lines.join("\n");
    } else {
      promptInput.value = `${command}\n${current}`;
    }
  }

  promptInput.focus();
}

function migrateLegacyHistory() {
  if (localStorage.getItem(HISTORY_KEY)) {
    return;
  }

  for (const key of LEGACY_HISTORY_KEYS) {
    const legacy = localStorage.getItem(key);
    if (legacy) {
      localStorage.setItem(HISTORY_KEY, legacy);
      return;
    }
  }
}

function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
  } catch {
    return [];
  }
}

function saveHistory(prompt, data) {
  const history = getHistory();
  const item = {
    prompt,
    mode: data.mode || "general",
    agent: data.agent || "general",
    provider: data.provider || "unknown",
    model: data.model || "unknown",
    responseTimeSec: Number.isFinite(data.response_time_sec)
      ? data.response_time_sec
      : null,
    version: data.version || APP_VERSION,
    createdAt: new Date().toLocaleString("ko-KR"),
  };

  const nextHistory = [item, ...history].slice(0, 12);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
}

function renderHistory() {
  const history = getHistory();

  if (!history.length) {
    historyList.innerHTML = '<p class="empty-history">아직 기록이 없습니다.</p>';
    return;
  }

  historyList.innerHTML = "";

  history.forEach((item) => {
    const div = document.createElement("div");
    div.className = "history-item";
    const timeText = Number.isFinite(item.responseTimeSec)
      ? `${item.responseTimeSec}s`
      : "-";

    div.innerHTML = `
      <div class="history-item-top">
        <span>${escapeHtml(item.agent)} · ${escapeHtml(item.provider)} · ${escapeHtml(item.model)}</span>
        <span>${escapeHtml(timeText)}</span>
      </div>
      <p>${escapeHtml(item.prompt)}</p>
      <p class="history-meta">${escapeHtml(item.createdAt)} · ${escapeHtml(item.version)}</p>
    `;

    div.addEventListener("click", () => {
      promptInput.value = item.prompt;
      modeValue.textContent = item.mode;
      agentValue.textContent = item.agent;
      providerValue.textContent = item.provider;
      modelValue.textContent = item.model;
      timeValue.textContent = Number.isFinite(item.responseTimeSec)
        ? `${item.responseTimeSec}s`
        : "-";
      versionValue.textContent = item.version;
      setStatus("idle", "Loaded");
    });

    historyList.appendChild(div);
  });
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
  setStatus("idle", "History Cleared");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.querySelectorAll(".quick-btn").forEach((button) => {
  button.addEventListener("click", () => {
    insertCommand(button.dataset.command);
  });
});

runBtn.addEventListener("click", runAgent);
clearBtn.addEventListener("click", clearInput);
copyBtn.addEventListener("click", copyOutput);
approveBtn.addEventListener("click", approvePendingAction);
cancelApprovalBtn.addEventListener("click", () => cancelPendingAction(false));
clearHistoryBtn.addEventListener("click", clearHistory);

promptInput.addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") {
    runAgent();
  }
});

migrateLegacyHistory();
renderHistory();
setStatus("idle", "Ready");
