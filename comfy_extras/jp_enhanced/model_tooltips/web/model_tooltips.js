import { app } from "../../scripts/app.js";

const catalog = new Map();
const attached = new WeakSet();
const inputTooltips = new Map();
const descriptions = new Set();
const categories = {
  ckpt_name: "checkpoints",
  unet_name: "diffusion_models",
  vae_name: "vae",
  lora_name: "loras",
  control_net_name: "controlnet",
  sam3_model: "sam3",
};

function normalize(value) {
  return value.replaceAll("\\", "/");
}

async function loadJson(path) {
  const response = await fetch(new URL(path, import.meta.url));
  if (!response.ok) throw new Error(`モデル説明を読み込めませんでした: ${path}`);
  return response.json();
}

function modelDescription(entry, filename) {
  return [
    entry.name,
    `作者: ${entry.author}`,
    entry.publisher && `変換・配布: ${entry.publisher}`,
    `対応: ${entry.baseModel}`,
    entry.description,
    entry.notes && `注意: ${entry.notes}`,
    `確認: ${entry.verification}`,
    `ファイル: ${filename}`,
    entry.sources.length && `出典: ${entry.sources.join("\n")}`,
  ].filter(Boolean).join("\n");
}

function setupModelTooltip() {
  const panel = document.createElement("div");
  panel.className = "jp-model-tooltip";
  panel.hidden = true;
  panel.setAttribute("role", "tooltip");
  const style = document.createElement("style");
  style.textContent = `
    .jp-model-tooltip {
      position: fixed; z-index: 10000; box-sizing: border-box;
      width: min(520px, calc(100vw - 24px)); max-height: calc(100vh - 24px);
      padding: 14px 16px; border: 1px solid #777; border-radius: 8px;
      background: #252525; color: #f4f4f4; box-shadow: 0 4px 16px #0006;
      font: 14px/1.65 sans-serif; white-space: pre-wrap; overflow-wrap: anywhere;
      overflow-y: auto; overscroll-behavior: contain; user-select: text;
    }
    .jp-model-tooltip[hidden] { display: none; }
    .node-tooltip.jp-model-tooltip-source { visibility: hidden; }
  `;
  document.head.append(style);
  document.body.append(panel);
  let x = 12, y = 12, hideTimer;
  function place() {
    const rect = panel.getBoundingClientRect();
    panel.style.left = `${Math.max(12, Math.min(x + 12, window.innerWidth - rect.width - 12))}px`;
    panel.style.top = `${Math.max(12, Math.min(y + 12, window.innerHeight - rect.height - 12))}px`;
  }
  function hide() {
    clearTimeout(hideTimer);
    panel.hidden = true;
  }
  document.addEventListener("mousemove", (event) => { x = event.clientX; y = event.clientY; });
  panel.addEventListener("mousemove", (event) => event.stopPropagation());
  panel.addEventListener("mouseenter", () => clearTimeout(hideTimer));
  panel.addEventListener("mouseleave", hide);
  panel.addEventListener("click", (event) => event.stopPropagation());
  panel.addEventListener("wheel", (event) => event.stopPropagation());
  window.addEventListener("resize", place);
  window.addEventListener("keydown", (event) => { if (event.key === "Escape") hide(); });
  const observer = new MutationObserver(() => {
    const source = document.querySelector(".node-tooltip");
    const text = source?.textContent;
    if (text && descriptions.has(text)) {
      source.classList.add("jp-model-tooltip-source");
      clearTimeout(hideTimer);
      if (panel.textContent !== text || panel.hidden) {
        panel.textContent = text;
        panel.scrollTop = 0;
        panel.hidden = false;
        place();
      }
    } else {
      source?.classList.remove("jp-model-tooltip-source");
      if (!panel.hidden && !panel.matches(":hover")) {
        clearTimeout(hideTimer);
        hideTimer = setTimeout(hide, 200);
      }
    }
  });
  observer.observe(document.body, { subtree: true, childList: true, characterData: true });
}

function attachTooltips(node) {
  for (const widget of node.widgets ?? []) {
    if (attached.has(widget)) continue;
    const category = categories[widget.name]
      ?? (/^clip_name\d*$/.test(widget.name) ? "text_encoders" : undefined)
      ?? (widget.name === "model_name" && node.comfyClass === "UpscaleModelLoader" ? "upscale_models" : undefined);
    if (!category) continue;
    const descriptor = Object.getOwnPropertyDescriptor(widget, "tooltip");
    if (descriptor?.configurable === false) continue;
    let original = widget.tooltip ?? inputTooltips.get(node.comfyClass)?.get(widget.name);
    Object.defineProperty(widget, "tooltip", {
      configurable: true,
      enumerable: descriptor?.enumerable ?? true,
      get() {
        const previous = descriptor?.get ? descriptor.get.call(this) : original;
        if (typeof this.value !== "string") return previous;
        const filename = normalize(this.value);
        if (!/\.(safetensors|gguf|ckpt|pt|pth|bin)$/i.test(filename)) return previous;
        const entry = catalog.get(`${category}/${filename}`);
        const description = entry ? modelDescription(entry, filename) : `ファイル: ${filename}\nこのファイルの説明は未登録です。`;
        const text = [description, previous].filter(Boolean).join("\n\n");
        descriptions.add(text);
        return text;
      },
      set(value) {
        if (descriptor?.set) descriptor.set.call(this, value);
        else original = value;
      },
    });
    attached.add(widget);
  }
}

app.registerExtension({
  name: "JPEnhanced.ModelTooltips",
  setup: setupModelTooltip,
  beforeRegisterNodeDef(nodeType, nodeData) {
    const descriptions = new Map();
    for (const inputs of [nodeData.input?.required, nodeData.input?.optional]) {
      for (const [name, spec] of Object.entries(inputs ?? {})) {
        if (spec[1]?.tooltip) descriptions.set(name, spec[1].tooltip);
      }
    }
    inputTooltips.set(nodeData.name, descriptions);
  },
  async init() {
    try {
      const manifest = await loadJson("./catalog/index.json");
      await Promise.all(manifest.files.map(async (path) => {
        const group = await loadJson(`./catalog/${path}`);
        for (const entry of group.models) {
          catalog.set(`${group.category}/${normalize(entry.file)}`, entry);
        }
      }));
    } catch (error) {
      console.warn(error.message);
    }
  },
  nodeCreated: attachTooltips,
  loadedGraphNode: attachTooltips,
});
