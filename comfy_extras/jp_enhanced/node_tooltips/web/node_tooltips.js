import { app } from "../../scripts/app.js";

let nodeEntries = [];

async function loadNodeEntries() {
  const response = await fetch(new URL("./nodes.ja.json", import.meta.url));
  if (!response.ok) {
    throw new Error("ノード別名辞書を読み込めませんでした。");
  }
  const dictionary = await response.json();
  if (dictionary.schemaVersion !== 1 || typeof dictionary.source !== "string" || typeof dictionary.license !== "string"
    || !Number.isInteger(dictionary.revision) || typeof dictionary.updatedAt !== "string" || !Array.isArray(dictionary.changes)
    || !Array.isArray(dictionary.nodes)) {
    throw new Error("ノード別名辞書の形式が正しくありません。");
  }
  if (!dictionary.nodes.every((entry) => {
    return typeof entry.node === "string" && typeof entry.ja === "string" && typeof entry.description === "string"
      && typeof entry.category === "string" && Array.isArray(entry.aliases)
      && entry.aliases.every((alias) => typeof alias === "string");
  })) {
    throw new Error("ノード別名辞書に不正な項目があります。");
  }
  nodeEntries = dictionary.nodes;
}

app.registerExtension({
  name: "JPEnhanced.NodeTooltips",
  async init() {
    try {
      await loadNodeEntries();
    } catch (error) {
      console.warn(error.message);
    }
  },
  beforeRegisterNodeDef(nodeType, nodeData) {
    const entry = nodeEntries.find((item) => item.node === nodeData.name);
    if (entry) {
      nodeData.description = [entry.description, nodeData.description].filter(Boolean).join("\n\n");
    }
  },
});
