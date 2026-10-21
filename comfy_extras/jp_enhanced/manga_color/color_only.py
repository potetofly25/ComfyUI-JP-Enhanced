import torch
import torch.nn.functional as F


class JPMangaColorOnly:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "original": ("IMAGE",),
            "colored": ("IMAGE",),
            "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
        }, "optional": {
            "mask": ("MASK",),
            "color_mode": (["Original brightness", "Reference RGB"], {"default": "Original brightness"}),
            "ink_radius": ("INT", {"default": 0, "min": 0, "max": 16, "tooltip": "Reference RGB用。色画像の細い暗線を周囲の色で除去する半径px。大きいと色境界や細部が広がります。"}),
        }}

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply"
    CATEGORY = "JP Enhanced/Manga Color"
    DESCRIPTION = "Original brightnessは生成画像の色相・彩度のみを使用。Reference RGBは暗い色も維持して元ページの黒線・トーンを乗算します。生成された有彩色の二重線や色むらは残ります。ink_radiusは細い暗線を除去しますが、色境界も広がります。マスクは白が着色、黒が元画像維持。"

    def apply(self, original, colored, strength, mask=None, color_mode="Original brightness", ink_radius=0):
        source = original[..., :3]
        color = colored[..., :3].to(device=source.device, dtype=source.dtype)
        if color.shape[1:3] != source.shape[1:3]:
            color = F.interpolate(color.movedim(-1, 1), size=source.shape[1:3], mode="bilinear", align_corners=False).movedim(1, -1)
        if color_mode == "Reference RGB":
            if ink_radius:
                color = F.max_pool2d(color.movedim(-1, 1), 2 * ink_radius + 1, stride=1, padding=ink_radius).movedim(1, -1)
            tinted = source.amax(dim=-1, keepdim=True) * color
        else:
            # Discard generated brightness, including newly drawn black lines and shadows.
            maximum = color.amax(dim=-1, keepdim=True)
            hue = torch.where(maximum > 0, color / maximum.clamp_min(torch.finfo(color.dtype).tiny), torch.ones_like(color))
            tinted = source.amax(dim=-1, keepdim=True) * hue
        weight = strength
        if mask is not None:
            weight = mask.to(device=source.device, dtype=source.dtype).reshape(-1, 1, *mask.shape[-2:])
            weight = F.interpolate(weight, size=source.shape[1:3], mode="bilinear", align_corners=False).movedim(1, -1).clamp(0, 1) * strength
        return (source + (tinted - source) * weight,)


class JPMangaReferenceFill:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image": ("IMAGE",),
            "original": ("IMAGE",),
            "reference": ("IMAGE",),
            "mask": ("MASK",),
            "reference_x": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.001, "tooltip": "参考画像の採色位置。左端0、右端1。"}),
            "reference_y": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.001, "tooltip": "参考画像の採色位置。上端0、下端1。影や輪郭を避け、色が均一な所を指定。"}),
            "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
        }}

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply"
    CATEGORY = "JP Enhanced/Manga Color"
    DESCRIPTION = "白いマスク範囲へ参考画像の指定位置のRGB色を直接塗ります。元ページの黒線とトーンを乗算で保持します。マスクの外は入力の着色結果を保持します。別の色はこのノードを複製して直列に接続してください。"

    def apply(self, image, original, reference, mask, reference_x, reference_y, strength):
        source = original[..., :3].to(device=image.device, dtype=image.dtype)
        x = round(reference_x * (reference.shape[2] - 1))
        y = round(reference_y * (reference.shape[1] - 1))
        color = reference[:, y:y + 1, x:x + 1, :3].to(device=image.device, dtype=image.dtype)
        ink = source.amax(dim=-1, keepdim=True)
        filled = ink * color
        weight = mask.to(device=image.device, dtype=image.dtype).reshape(-1, 1, *mask.shape[-2:])
        weight = F.interpolate(weight, size=image.shape[1:3], mode="bilinear", align_corners=False).movedim(1, -1).clamp(0, 1) * strength
        return (image[..., :3] + (filled - image[..., :3]) * weight,)
