import { app } from "/scripts/app.js";

function arrangeImages(node) {
    for (const input of node.inputs ?? []) {
        if (input.name === "english" || input.name === "negative_english") {
            input.label = input.name === "english" ? "Positive 英語" : "Negative 英語";
            input.localized_name = input.label;
        }
    }
    if (node.comfyClass !== "JPQwenImage21SpectrumImageEdit") {
        node.setDirtyCanvas(true, true);
        return;
    }
    const names = ["image", "image_2", "image_3", "image_4", "image_5"];
    for (let slot = node.inputs.length - 1; slot >= 0; slot--) {
        const input = node.inputs[slot];
        if (!input.name.startsWith("references.")) continue;
        const target = node.inputs.find(candidate => candidate.name === input.name.slice(11));
        if (input.link != null && target && target.link == null) {
            target.link = input.link;
            input.link = null;
        }
        if (input.link == null) node.removeInput(slot);
    }
    const images = names.map(name => node.inputs?.find(input => input.name === name)).filter(Boolean);
    if (!images.length) return;
    node.inputs = [...images, ...node.inputs.filter(input => !names.includes(input.name))];
    for (const input of images) {
        const number = input.name === "image" ? 1 : Number(input.name.slice(6));
        input.label = number === 1 ? "Image1 編集対象" : `Image${number} 参照画像（参照要素をプロンプトで明示）`;
    }
    node.inputs.forEach((input, slot) => {
        const link = node.graph?.links[input.link];
        if (link) link.target_slot = slot;
    });
    node.setDirtyCanvas(true, true);
}

app.registerExtension({
    name: "JPEnhanced.QwenImageInputs",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!["JPQwenImage21SpectrumImageEdit", "JPQwenImage21SpectrumTextToImage"].includes(nodeData.name)) return;
        const onCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function (...args) {
            const result = onCreated?.apply(this, args);
            arrangeImages(this);
            return result;
        };
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const bindings = new Map((info.inputs ?? []).map(input => [input.name, input.link]));
            const result = onConfigure?.call(this, info);
            // Preserve serialized connections by socket name while restoring display order.
            for (const input of this.inputs ?? []) {
                if (bindings.has(input.name)) input.link = bindings.get(input.name);
            }
            arrangeImages(this);
            return result;
        };
    }
});
