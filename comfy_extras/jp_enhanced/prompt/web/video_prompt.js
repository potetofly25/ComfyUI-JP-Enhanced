import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "JPEnhanced.VideoPrompt",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "JPVideoPromptJapanese") return;
        const onCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onCreated?.apply(this, arguments);
            const button = this.addWidget("button", "表示した下書きを確定（次の実行で動画生成）", null, () => {
                const preview = this.widgets?.find(w => w.name === "変換結果（確認して確定欄へコピー）");
                const edited = this.widgets?.find(w => w.name === "edited_prompt");
                const mode = this.widgets?.find(w => w.name === "mode");
                if (!preview?.value || !edited || !mode || mode.value !== "Draft only") return;
                edited.value = preview.value;
                mode.value = "Use edited prompt";
                edited.callback?.(edited.value);
                mode.callback?.(mode.value);
                this.setDirtyCanvas(true, true);
            });
            button.serialize = false;
        };
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);
            let preview = this.widgets?.find(w => w.name === "変換結果（確認して確定欄へコピー）");
            if (!preview) {
                preview = ComfyWidgets.STRING(this, "変換結果（確認して確定欄へコピー）", ["STRING", { multiline: true }], app).widget;
                preview.inputEl.readOnly = true;
                preview.serialize = false;
            }
            preview.value = (message.text ?? []).join("\n");
            this.setDirtyCanvas(true, true);
        };
    },
});
