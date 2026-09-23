import asyncio
import unittest
from unittest.mock import Mock

from comfy_extras.jp_enhanced.prompt import JPEnhancedEnglishPrompt, comfy_entrypoint


def test_translation_orders_inputs_and_preserves_generation_settings():
    clip = Mock()
    clip.decode.return_value = "<think>internal\nreasoning</think> Keep the same face. "
    result = JPEnhancedEnglishPrompt.execute(
        clip, {"text_10": "背景", "text_2": "服装", "text_0": "人物", "text_1": "  "},
        "Translate. /no_think\n\n", "Clean photograph.\n", 768,
    )
    assert result.result == ("Clean photograph.\nKeep the same face.",)
    clip.tokenize.assert_called_once_with(
        "Translate. /no_think\n\n人物\n服装\n背景", image=None, skip_template=False,
        min_length=1, thinking=False, video=None, audio=None,
    )
    clip.generate.assert_called_once_with(
        clip.tokenize.return_value, do_sample=False, max_length=768, temperature=1.0,
        top_k=50, top_p=1.0, min_p=0.0, repetition_penalty=1.0,
        presence_penalty=0.0, seed=None,
    )


def test_empty_translation_does_not_send_only_prefix_to_generation():
    for generated in ["", "<THINK>unfinished reasoning", "<think>reasoning</think>\n"]:
        clip = Mock()
        clip.decode.return_value = generated
        with unittest.TestCase().assertRaisesRegex(ValueError, "英訳結果が空"):
            JPEnhancedEnglishPrompt.execute(clip, {"text_0": "人物"}, "Translate", "Quality", 768)


def test_blank_input_does_not_run_model():
    clip = Mock()
    assert JPEnhancedEnglishPrompt.execute(clip, {"text_0": " \n"}, "Translate", "", 768).result == ("",)
    clip.tokenize.assert_not_called()


def test_plain_translation_without_prefix():
    clip = Mock()
    clip.decode.return_value = "A person in a park."
    assert JPEnhancedEnglishPrompt.execute(clip, {"text_0": "公園の人物"}, "Translate", "", 768).result == ("A person in a park.",)


def test_extension_exposes_common_node():
    extension = asyncio.run(comfy_entrypoint())
    assert asyncio.run(extension.get_node_list()) == [JPEnhancedEnglishPrompt]
    schema = JPEnhancedEnglishPrompt.INPUT_TYPES()
    assert schema["optional"]["texts"][0] == "COMFY_AUTOGROW_V3"


def test_raw_tags_bypass_translation_and_keep_weight_syntax():
    clip = Mock()
    clip.decode.return_value = "A person in a park."
    tags = r"  (sharp focus:1.2), artist_name, \(literal\)" + "\n[soft light]  "
    result = JPEnhancedEnglishPrompt.execute(clip, {"text_0": "公園の人物"}, "Translate", "Photo.", 768, tags)
    assert result.result == ("Photo.\nA person in a park.\n" + tags,)
    assert tags not in clip.tokenize.call_args.args[0]


def test_raw_only_and_empty_negative_do_not_require_clip():
    assert JPEnhancedEnglishPrompt.execute().result == ("",)
    assert JPEnhancedEnglishPrompt.execute(english_suffix="(blur:1.2), watermark").result == ("(blur:1.2), watermark",)


def test_japanese_requires_translation_clip():
    with unittest.TestCase().assertRaisesRegex(ValueError, "翻訳用CLIP"):
        JPEnhancedEnglishPrompt.execute(texts={"text_0": "ぼけ"})
