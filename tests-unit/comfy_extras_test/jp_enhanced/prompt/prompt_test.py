import asyncio
import unittest
from unittest.mock import Mock

from comfy_extras.jp_enhanced.prompt import JPEnhancedEnglishPrompt, JPScenePromptJapanese, JPScenePromptEnglish, JPVideoPromptJapanese, comfy_entrypoint


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
        min_length=1, thinking=False, video=None, audio=None, system_prompt="",
    )
    clip.generate.assert_called_once_with(
        clip.tokenize.return_value, do_sample=False, max_length=768, temperature=1.0,
        top_k=50, top_p=1.0, min_p=0.0, repetition_penalty=1.0,
        presence_penalty=0.0, seed=None, mtp=True,
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
    assert asyncio.run(extension.get_node_list()) == [JPEnhancedEnglishPrompt, JPScenePromptJapanese, JPScenePromptEnglish, JPVideoPromptJapanese]
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


def test_scene_english_keeps_weights_and_skips_blank_fields():
    assert JPScenePromptEnglish.execute("person", " (silk:1.2) ", "", "standing").result == ("person\n (silk:1.2) \nstanding",)


def test_scene_japanese_preserves_field_order():
    clip = Mock()
    clip.decode.return_value = "A person wearing a coat in a park, standing."
    result = JPScenePromptJapanese.execute("人物", "コート", "公園", "立つ", clip=clip)
    assert result.result == (clip.decode.return_value,)
    assert clip.tokenize.call_args.args[0].endswith("人物\nコート\n公園\n立つ")
    assert JPScenePromptJapanese.execute("", "", "", "").result == ("",)


def test_video_draft_protects_dialogue_and_blocks_generation():
    from comfy_execution.graph_utils import ExecutionBlocker
    clip = Mock()
    clip.decode.return_value = "integrated_multimodal_description: <Picture 1> waves.\noverall_soundscape: <d>[Japanese] __JP_DIALOGUE_0__</d>\nnon_diegetic_music: N/A"
    result = JPVideoPromptJapanese.execute('手を振って「こんにちは」と話す。BGMなし', clip=clip)
    assert isinstance(result.result[0], ExecutionBlocker)
    text = result.ui.as_dict()['text'][0]
    assert 'こんにちは' in text and '__JP_DIALOGUE_' not in text
    assert 'こんにちは' not in clip.tokenize.call_args.args[0]


def test_video_reviewed_text_is_exact_and_does_not_run_llm():
    clip = Mock()
    text = '  edited <d>[Japanese] こんにちは</d>\n'
    result = JPVideoPromptJapanese.execute('', 'Use edited prompt', text, clip=clip)
    assert result.result == (text,)
    clip.tokenize.assert_not_called()


def test_video_lost_dialogue_is_rejected():
    clip = Mock()
    for generated in ['truncated', 'integrated_multimodal_description: waves\noverall_soundscape: voice\nnon_diegetic_music: N/A']:
        clip.decode.return_value = generated
        with unittest.TestCase().assertRaises(ValueError):
            JPVideoPromptJapanese.execute('「こんにちは」と話す', clip=clip)


def test_video_convert_and_generate_returns_prompt_without_blocking():
    clip = Mock()
    clip.decode.return_value = "integrated_multimodal_description: <Picture 1> waves.\noverall_soundscape: <d>[Japanese] __JP_DIALOGUE_0__</d>\nnon_diegetic_music: N/A"
    result = JPVideoPromptJapanese.execute('手を振って「こんにちは」と話す。BGMなし', mode='Convert and generate', clip=clip)
    assert isinstance(result.result[0], str)
    assert 'こんにちは' in result.result[0]
    assert result.result[0] == result.ui.as_dict()['text'][0]


def test_video_missing_headings_do_not_raise_token_limit_error():
    clip = Mock()
    clip.decode.return_value = 'A person walks through a park.'
    result = JPVideoPromptJapanese.execute('公園を歩く', mode='Convert and generate', clip=clip).result[0]
    assert result == 'integrated_multimodal_description: A person walks through a park.\n\noverall_soundscape:\n\nnon_diegetic_music:'


def test_video_headings_accept_case_and_full_width_colon():
    clip = Mock()
    clip.decode.return_value = 'INTEGRATED_MULTIMODAL_DESCRIPTION： A park.\nOVERALL_SOUNDSCAPE : Wind.'
    result = JPVideoPromptJapanese.execute('公園。風の音', mode='Convert and generate', clip=clip).result[0]
    assert 'integrated_multimodal_description: A park.' in result
    assert 'overall_soundscape: Wind.' in result
    assert result.endswith('non_diegetic_music:')


def test_video_retranslates_japanese_instructions_before_restoring_dialogue():
    clip = Mock()
    clip.decode.side_effect = [
        'integrated_multimodal_description: <Picture 1> のキャラが手を振る\noverall_soundscape: __JP_DIALOGUE_0__\nnon_diegetic_music: N/A',
        'integrated_multimodal_description: The character from <Picture 1> waves.\noverall_soundscape: <d>[Japanese] __JP_DIALOGUE_0__</d>\nnon_diegetic_music: N/A',
    ]
    result = JPVideoPromptJapanese.execute('手を振り「こんにちは」と話す', mode='Convert and generate', clip=clip).result[0]
    assert clip.generate.call_count == 2
    assert 'のキャラ' not in result
    assert '<d>[Japanese] こんにちは</d>' in result
    assert 'こんにちは' not in clip.tokenize.call_args.args[0]


def test_video_english_instructions_do_not_trigger_second_translation():
    clip = Mock()
    clip.decode.return_value = 'integrated_multimodal_description: Waves.\noverall_soundscape: __JP_DIALOGUE_0__\nnon_diegetic_music: N/A'
    JPVideoPromptJapanese.execute('「こんにちは」', mode='Convert and generate', clip=clip)
    assert clip.generate.call_count == 1
