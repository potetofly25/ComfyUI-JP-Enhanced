import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

let errorGuideData = null;
let latestExecutionError = null;
let errorGuidePanel = null;
let guidePanel = null;
const localSession = ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname);

function button(label, onClick) {
  const element = document.createElement("button");
  element.type = "button";
  element.textContent = label;
  element.addEventListener("click", onClick);
  return element;
}

async function copyText(value) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch {
    }
  }
  const temporary = document.createElement("textarea");
  temporary.value = value;
  temporary.setAttribute("readonly", "");
  temporary.style.position = "fixed";
  temporary.style.left = "-9999px";
  document.body.append(temporary);
  temporary.select();
  try {
    return document.execCommand("copy");
  } finally {
    temporary.remove();
  }
}

function clearSection(section) {
  const heading = section.querySelector(":scope > h3");
  section.replaceChildren();
  if (heading) {
    section.append(heading);
  }
}

function createSection(title) {
  const section = document.createElement("section");
  const heading = document.createElement("h3");
  heading.textContent = title;
  section.append(heading);
  return section;
}

async function loadErrorGuides() {
  const response = await fetch(new URL("./errors.ja.json", import.meta.url));
  if (!response.ok) {
    throw new Error("エラーガイドを読み込めませんでした。");
  }
  const documentValue = await response.json();
  if (documentValue.schemaVersion !== 1 || !Number.isInteger(documentValue.revision) || !Array.isArray(documentValue.guides) || !documentValue.unknownGuide) {
    throw new Error("エラーガイドの形式が正しくありません。");
  }
  const isStringList = (values) => Array.isArray(values) && values.every((value) => typeof value === "string");
  const hasGuideText = (guide) => guide && typeof guide.id === "string" && typeof guide.summary === "string"
    && isStringList(guide.causes) && isStringList(guide.checks) && isStringList(guide.actions)
    && typeof guide.confidence === "string" && Number.isInteger(guide.revision);
  if (!hasGuideText(documentValue.unknownGuide)) {
    throw new Error("エラーガイドの形式が正しくありません。");
  }
  if (!documentValue.guides.every((guide) => hasGuideText(guide) && isStringList(guide.exceptionTypes) && isStringList(guide.messageIncludes))) {
    throw new Error("エラーガイドに不正な項目があります。");
  }
  errorGuideData = documentValue;
}

function selectErrorGuide(error) {
  if (!errorGuideData) {
    return null;
  }
  const exceptionType = error.exception_type || "";
  const byType = errorGuideData.guides.find((guide) => guide.exceptionTypes.includes(exceptionType));
  if (byType) {
    return byType;
  }
  const message = (error.exception_message || "").toLowerCase();
  return errorGuideData.guides.find((guide) => guide.messageIncludes.some((term) => message.includes(term))) || errorGuideData.unknownGuide;
}

function appendGuideList(container, title, values, open = false) {
  const details = document.createElement("details");
  details.open = open;
  const heading = document.createElement("summary");
  heading.textContent = title;
  const list = document.createElement("ul");
  for (const value of values) {
    const item = document.createElement("li");
    item.textContent = value;
    list.append(item);
  }
  details.append(heading, list);
  container.append(details);
}

function sanitizeDiagnosticText(value) {
  return value
    .replace(/((?:positive|negative|prompt)\s*(?:=|:)\s*)(?:"[^"]*"|'[^']*'|[^\n\r,]+)/gi, "$1[Promptを除外]")
    .replace(/[A-Za-z]:\\[^\n\r"']+/g, "[ローカルパス]")
    .replace(/\\\\[^\s\\]+\\[^\s]+/g, "[ローカルパス]")
    .replace(/\/(?:[^\s/:]+\/){2,}[^\s/:]*/g, "[ローカルパス]");
}

function diagnosticText(guide) {
  return [
    `JP-Enhanced バージョン: 0.1.0`,
    `ガイドID: ${guide.id}`,
    `ガイド改訂: ${guide.revision}`,
    `失敗ノード種別: ${latestExecutionError.node_type || "不明"}`,
    `例外種別: ${latestExecutionError.exception_type || "不明"}`,
    "",
    "英語原文:",
    sanitizeDiagnosticText(latestExecutionError.exception_message || "原文メッセージはありません。"),
  ].join("\n");
}

function showDiagnosticCopyDialog(guide) {
  const dialog = document.createElement("dialog");
  const title = document.createElement("h3");
  title.textContent = "ローカル診断情報を確認";
  const notice = document.createElement("p");
  notice.textContent = "この内容は自動送信されません。Prompt・画像・不要な絶対パスは含めません。";
  const preview = document.createElement("textarea");
  preview.readOnly = true;
  preview.rows = 12;
  preview.value = diagnosticText(guide);
  const close = button("閉じる", () => dialog.close());
  const copy = button("クリップボードへコピー", async () => {
    if (await copyText(preview.value)) {
      dialog.close();
    } else {
      preview.focus();
      preview.select();
      window.alert("コピーできませんでした。内容を選択してコピーしてください。");
    }
  });
  dialog.append(title, notice, preview, close, copy);
  dialog.addEventListener("close", () => dialog.remove(), { once: true });
  document.body.append(dialog);
  dialog.showModal();
}

function renderErrorGuide(container) {
  clearSection(container);
  if (!latestExecutionError) {
    const message = document.createElement("p");
    message.textContent = "実行エラーが発生すると、英語原文を残した日本語ガイドをここに表示します。";
    container.append(message);
    return;
  }
  const guide = selectErrorGuide(latestExecutionError);
  if (!guide) {
    const message = document.createElement("p");
    message.textContent = "エラーガイドを読み込めませんでした。英語原文を確認してください。";
    container.append(message);
    return;
  }
  const originalTitle = document.createElement("h4");
  originalTitle.textContent = "英語原文";
  const original = document.createElement("pre");
  original.textContent = latestExecutionError.exception_message || "原文メッセージはありません。";
  const node = document.createElement("p");
  node.textContent = `失敗ノード: ${latestExecutionError.node_type || "不明"} / 例外種別: ${latestExecutionError.exception_type || "不明"}`;
  const summary = document.createElement("p");
  summary.textContent = guide.summary;
  const confidence = document.createElement("p");
  confidence.textContent = `案内の確度: ${guide.confidence}`;
  const revision = document.createElement("p");
  revision.textContent = `ガイドID: ${guide.id} / 改訂: ${guide.revision}`;
  container.append(originalTitle, original, node, summary);
  appendGuideList(container, "考えられる原因", guide.causes);
  appendGuideList(container, "確認してください", guide.checks, true);
  appendGuideList(container, "対処方法", guide.actions, true);
  container.append(confidence, revision, button("診断情報を確認してコピー", () => showDiagnosticCopyDialog(guide)));
  if (localSession) {
    container.append(button("ローカルログを開く", openLocalLogs));
  }
}

function showExecutionErrorNotice() {
  document.getElementById("jp-enhanced-error-notice")?.remove();
  const notice = document.createElement("div");
  notice.id = "jp-enhanced-error-notice";
  notice.className = "jp-enhanced-error-notice";
  notice.setAttribute("role", "status");
  const message = document.createElement("span");
  message.textContent = "実行エラーの日本語ガイドを更新しました。";
  const openGuide = button("ガイドを開く", () => {
    notice.remove();
    guidePanel.hidden = false;
  });
  const dismiss = button("閉じる", () => notice.remove());
  notice.append(message, openGuide, dismiss);
  document.body.append(notice);
}

function openLocalLogs() {
  window.open("/internal/logs", "_blank", "noopener,noreferrer");
}

function recordExecutionError(detail) {
  if (!detail || typeof detail !== "object") {
    return;
  }
  latestExecutionError = {
    exception_type: typeof detail.exception_type === "string" ? detail.exception_type : "",
    exception_message: typeof detail.exception_message === "string" ? detail.exception_message : "",
    node_type: typeof detail.node_type === "string" ? detail.node_type : "",
  };
  if (errorGuidePanel) {
    renderErrorGuide(errorGuidePanel);
  }
  showExecutionErrorNotice();
}

app.registerExtension({
  name: "JPEnhanced.ErrorSupport",
  async setup() {
    const style = document.createElement("style");
    style.textContent = `
      #jp-enhanced-error-launcher { position: fixed; right: 16px; bottom: 80px; z-index: 10000; }
      #jp-enhanced-error-guide { position: fixed; right: 16px; bottom: 120px; z-index: 10000; box-sizing: border-box; width: min(480px, calc(100vw - 32px)); max-height: calc(100dvh - 144px); overflow: auto; padding: 16px; color: #f5f5f5; background: #252525; border: 1px solid #666; border-radius: 8px; }
      #jp-enhanced-error-guide[hidden] { display: none; }
      #jp-enhanced-error-guide pre { white-space: pre-wrap; overflow-wrap: anywhere; }
      .jp-enhanced-error-notice { position: fixed; right: 16px; top: 80px; z-index: 10001; max-width: calc(100vw - 32px); padding: 12px; color: #f5f5f5; background: #7f1d1d; border: 1px solid #ef4444; border-radius: 8px; }
    `;
    document.head.append(style);
    guidePanel = createSection("実行エラーの日本語ガイド");
    guidePanel.id = "jp-enhanced-error-guide";
    guidePanel.hidden = true;
    guidePanel.setAttribute("aria-label", "実行エラーの日本語ガイド");
    guidePanel.append(button("閉じる", () => { guidePanel.hidden = true; }));
    errorGuidePanel = document.createElement("section");
    guidePanel.append(errorGuidePanel);
    guidePanel.addEventListener("keydown", (event) => {
      if (event.key === "Escape") guidePanel.hidden = true;
    });
    const launcher = button("エラー支援", () => { guidePanel.hidden = !guidePanel.hidden; });
    launcher.id = "jp-enhanced-error-launcher";
    document.body.append(launcher, guidePanel);
    api.addEventListener("execution_error", (event) => recordExecutionError(event.detail));
    renderErrorGuide(errorGuidePanel);
    try {
      await loadErrorGuides();
      renderErrorGuide(errorGuidePanel);
    } catch (error) {
      errorGuidePanel.textContent = error.message;
    }
  },
});
