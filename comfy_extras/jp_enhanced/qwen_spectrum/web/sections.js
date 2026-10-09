import { app } from "/scripts/app.js";

const types = new Set(["JPQwenImage21SpectrumTextToImage", "JPQwenImage21SpectrumImageEdit"]);
const widgetGroups = {
    seed: ["KSampler ｜ サンプリング設定", "#8a7343"],
    width: ["EmptyLatentImage ｜ 出力サイズ", "#8a7343"],
    resolution: ["TextEncodeQwenImage21 ｜ 参照画像の解像度", "#3e778b"],
    spectrum_enabled: ["Spectrum ｜ 近似高速化設定", "#685489"],
};

function drawHeading(ctx, width, y, title, color) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.fillRect(12, y, width - 24, 25);
    ctx.font = "bold 12px sans-serif";
    ctx.textAlign = "left";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(title, 20, y + 17, width - 40);
    ctx.restore();
}

function layoutHeaders(node, widgets) {
    const layout = [];
    node.jpSectionHeaders = [];
    for (const widget of widgets) {
        const group = widgetGroups[widget.name];
        if (group) {
            const header = { computeSize: () => [0, 30], group };
            layout.push(header);
            node.jpSectionHeaders.push(header);
        }
        layout.push(widget);
    }
    return layout;
}

app.registerExtension({
    name: "JPEnhanced.QwenSections",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!types.has(nodeData.name)) return;
        // Layout-only rows are never inserted into node.widgets or serialized.
        const getLayout = nodeType.prototype.getLayoutWidgets;
        nodeType.prototype.getLayoutWidgets = function (...args) {
            return layoutHeaders(this, getLayout.apply(this, args));
        };
        const computeSize = nodeType.prototype.computeSize;
        nodeType.prototype.computeSize = function (...args) {
            const size = computeSize.apply(this, args);
            size[1] += (this.widgets ?? []).filter(w => !w.hidden && widgetGroups[w.name]).length * 34;
            return size;
        };
        const foreground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx, ...args) {
            foreground?.call(this, ctx, ...args);
            if (this.flags.collapsed) return;
            for (const header of this.jpSectionHeaders ?? []) {
                if (Number.isFinite(header.y)) drawHeading(ctx, this.size[0], header.y + 2, ...header.group);
            }
        };
    }
});
