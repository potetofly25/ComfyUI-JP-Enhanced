import importlib.util
from pathlib import Path

import torch


spec = importlib.util.spec_from_file_location("manga_color_only", Path(__file__).resolve().parents[4] / "comfy_extras/jp_enhanced/manga_color/color_only.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_preserves_ink_tones_and_discards_generated_dark_lines():
    source = torch.tensor([0.0, 0.25, 1.0, 1.0]).reshape(1, 1, 4, 1).expand(-1, -1, -1, 3)
    color = torch.tensor([[[[1.0, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.0], [0.2, 0.1, 0.0]]]])
    result = module.JPMangaColorOnly().apply(source, color, 1.0)[0]
    torch.testing.assert_close(result.amax(-1), source.amax(-1))
    torch.testing.assert_close(result[0, 0, 0], torch.zeros(3))
    torch.testing.assert_close(result[0, 0, 2], torch.ones(3))
    torch.testing.assert_close(result[0, 0, 3], torch.tensor([1.0, 0.5, 0.0]))


def test_mask_strength_resize_and_rgba():
    source = torch.ones(1, 4, 4, 3)
    color = torch.tensor([[[[1.0, 0.0, 0.0, 0.3]]]])
    node = module.JPMangaColorOnly()
    torch.testing.assert_close(node.apply(source, color, 0.0)[0], source)
    torch.testing.assert_close(node.apply(source, color, 1.0, torch.zeros(1, 2, 2))[0], source)
    result = node.apply(source, color, 0.5, torch.ones(1, 2, 2))[0]
    torch.testing.assert_close(result, torch.tensor([1.0, 0.5, 0.5]).expand_as(source))


def test_reference_fill_keeps_dark_reference_color_and_original_ink():
    original = torch.tensor([0.0, 0.5, 1.0, 1.0]).reshape(1, 1, 4, 1).expand(-1, -1, -1, 3)
    generated = torch.ones_like(original)
    reference = torch.tensor([[[[1.0, 0.0, 0.0], [0.1, 0.2, 0.3]]]])
    mask = torch.tensor([[[1.0, 1.0, 1.0, 0.0]]])
    actual = module.JPMangaReferenceFill().apply(generated, original, reference, mask, 1.0, 0.0, 1.0)[0]
    expected = torch.tensor([[[[0.0, 0.0, 0.0], [0.05, 0.1, 0.15], [0.1, 0.2, 0.3], [1.0, 1.0, 1.0]]]])
    torch.testing.assert_close(actual, expected)


def test_reference_fill_resizes_mask_and_can_be_disabled():
    image = torch.rand(1, 4, 4, 3)
    original = torch.ones_like(image)
    reference = torch.tensor([[[[0.1, 0.2, 0.3, 0.5]]]])
    node = module.JPMangaReferenceFill()
    for mask, strength in [(torch.zeros(1, 2, 2), 1.0), (torch.ones(1, 2, 2), 0.0)]:
        torch.testing.assert_close(node.apply(image, original, reference, mask, 0.5, 0.5, strength)[0], image)
    actual = node.apply(image, original, reference, torch.ones(1, 2, 2), 0.5, 0.5, 1.0)[0]
    torch.testing.assert_close(actual, reference[..., :3].expand_as(image))


def test_rgb_transfer_preserves_dark_color_and_original_black():
    original = torch.ones(1, 5, 5, 3)
    original[:, 1, 1] = 0
    color = torch.tensor([0.1, 0.2, 0.3]).expand_as(original).clone()
    result = module.JPMangaColorOnly().apply(original, color, 1.0, color_mode="Reference RGB")[0]
    torch.testing.assert_close(result[:, 2, 2], color[:, 2, 2])
    torch.testing.assert_close(result[:, 1, 1], torch.zeros(1, 3))


def test_removed_color_layer_uses_original_brightness_for_saved_workflows():
    original = torch.ones(1, 1, 4, 3)
    original[:, :, 0] = 0
    color = torch.tensor([[[[0.8, 0.2, 0.1], [0.0, 0.0, 0.0], [0.3, 0.3, 0.3], [0.1, 0.2, 0.3]]]])
    result = module.JPMangaColorOnly().apply(original, color, 1.0, color_mode="Color layer")[0]
    torch.testing.assert_close(result[:, :, 0], torch.zeros(1, 1, 3))
    torch.testing.assert_close(result[:, :, 1:3], torch.ones(1, 1, 2, 3))
    torch.testing.assert_close(result[:, :, 3], color[:, :, 3] / 0.3)


def test_rgb_transfer_removes_thin_generated_ink_without_erasing_original_ink():
    original = torch.ones(1, 5, 5, 3)
    original[:, 1, :] = 0
    color = torch.tensor([0.1, 0.2, 0.3]).expand_as(original).clone()
    color[:, 2, :] = 0
    result = module.JPMangaColorOnly().apply(original, color, 1.0, color_mode="Reference RGB", ink_radius=1)[0]
    torch.testing.assert_close(result[:, 2, :], torch.tensor([0.1, 0.2, 0.3]).expand(1, 5, 3))
    torch.testing.assert_close(result[:, 1, :], torch.zeros(1, 5, 3))
