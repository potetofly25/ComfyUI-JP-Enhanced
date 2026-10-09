from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps


def image_paths(folder, image_load_cap=0, start_index=0, include_subfolders=False):
    root = Path(folder)
    if not folder.strip() or not root.is_dir():
        raise ValueError(f"Image folder not found: {folder}")
    entries = root.rglob("*") if include_subfolders else root.iterdir()
    paths = sorted(p for p in entries if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".tga"})
    paths = paths[start_index:]
    if image_load_cap:
        paths = paths[:image_load_cap]
    if not paths:
        raise ValueError("No images at the selected folder/start index.")
    return paths


def load_image(path):
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


class JPImageFolderList:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "folder": ("STRING", {"default": ""}),
            "image_load_cap": ("INT", {"default": 0, "min": 0}),
            "start_index": ("INT", {"default": 0, "min": 0}),
            "include_subfolders": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("IMAGE",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "load_images"
    CATEGORY = "JP Enhanced/image"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def load_images(self, folder, image_load_cap=0, start_index=0, include_subfolders=False):
        return ([load_image(path) for path in image_paths(folder, image_load_cap, start_index, include_subfolders)],)


NODE_CLASS_MAPPINGS = {"JPImageFolderList": JPImageFolderList}
NODE_DISPLAY_NAME_MAPPINGS = {"JPImageFolderList": "画像フォルダ読込（各画像の元サイズ）"}
