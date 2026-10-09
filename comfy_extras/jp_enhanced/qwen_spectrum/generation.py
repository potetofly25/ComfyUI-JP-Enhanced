import nodes
from comfy_api.latest import io
from comfy_extras.jp_enhanced.prompt import JPEnhancedEnglishPrompt, DEFAULT_TRANSLATION_RULES
from comfy_extras.nodes_qwen import TextEncodeQwenImage21

EDIT_RULES = (
    "Translate the image editing instructions into English. Preserve exactly what must "
    "change and what must stay unchanged. Preserve reference markers such as <image1> "
    "and <image2> exactly. Return only the translated instructions. /no_think"
)
NEGATIVE_RULES = (
    "Translate the unwanted image elements into English for a negative prompt. "
    "List only unwanted elements, not instructions to avoid them. "
    "Do not add details. Return only the English negative prompt. /no_think"
)


def prompt_inputs():
    return [
        io.Model.Input("model", display_name="画像生成モデル", tooltip="Qwen-Image 2.1を接続。safetensorsは拡散モデルローダー、GGUFはUnet Loader (GGUF)で読み込みます。"),
        io.Clip.Input("clip", display_name="生成用CLIP", tooltip="Qwen3-VL 8B / type=qwen_image。翻訳用CLIPとは別です。"),
        io.Vae.Input("vae", display_name="画像変換VAE", tooltip="Qwen-Image 2.1用VAE。"),
        io.Clip.Input("translation_clip", display_name="日本語翻訳用CLIP", optional=True, tooltip="日本語入力時のみ必要。Qwen3 4B / type=lumina2。"),
        io.String.Input("japanese", default="", force_input=True, display_name="Positive 日本語"),
        io.String.Input("english", default="", force_input=True, display_name="Positive 英語"),
        io.String.Input("negative_japanese", default="", force_input=True, display_name="Negative 日本語"),
        io.String.Input("negative_english", default="", force_input=True, display_name="Negative 英語"),
        io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
        io.Int.Input("steps", default=25, min=1, max=10000),
        io.Float.Input("cfg", default=1.0, min=0, max=100, step=0.1, tooltip="1ではNegativeは生成に作用しません。"),
        io.Combo.Input("sampler_name", options=nodes.KSampler.INPUT_TYPES()["required"]["sampler_name"][0], default="euler"),
        io.Combo.Input("scheduler", options=nodes.KSampler.INPUT_TYPES()["required"]["scheduler"][0], default="simple"),
    ]


def generate(model, clip, vae, japanese, english, negative_japanese, negative_english,
             seed, steps, cfg, sampler_name, scheduler, translation_clip, images, resolution, width=None, height=None):
    positive_text = JPEnhancedEnglishPrompt.execute(
        clip=translation_clip, texts={"text_0": japanese},
        translation_rules=EDIT_RULES if images else DEFAULT_TRANSLATION_RULES, english_suffix=english,
    ).result[0]
    negative_text = JPEnhancedEnglishPrompt.execute(
        clip=translation_clip, texts={"text_0": negative_japanese},
        translation_rules=NEGATIVE_RULES, english_suffix=negative_english,
    ).result[0]
    positive, negative, latent = TextEncodeQwenImage21.execute(
        clip, positive_text, negative_text, vae=vae, resolution=resolution, images=images,
    ).result
    if width is not None:
        latent = nodes.EmptyLatentImage().generate(width, height, 1)[0]
    samples = nodes.KSampler().sample(model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent)[0]
    return io.NodeOutput(nodes.VAEDecode().decode(vae, samples)[0], positive_text, negative_text)


class QwenTextToImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="QwenTextToImage", display_name="Qwen Image 2.1 画像生成",
            category="JP Enhanced/Qwen Image",
            inputs=prompt_inputs() + [
                io.Int.Input("width", display_name="出力幅", default=1024, min=32, max=nodes.MAX_RESOLUTION, step=32,
                             tooltip="入力に変換して解像度セレクターのwidthを接続できます。セレクターのmultipleは32に設定してください。"),
                io.Int.Input("height", display_name="出力高さ", default=1024, min=32, max=nodes.MAX_RESOLUTION, step=32,
                             tooltip="入力に変換して解像度セレクターのheightを接続できます。"),
            ], outputs=[
                io.Image.Output(),
                io.String.Output("positive_prompt", display_name="最終Positiveプロンプト",
                                 tooltip="翻訳・結合後、生成用CLIPへ渡したテキスト。任意でテキスト表示・保存ノードへ接続できます。"),
                io.String.Output("negative_prompt", display_name="最終Negativeプロンプト",
                                 tooltip="翻訳・結合後のNegativeテキスト。CFG=1でも出力しますが、生成には作用しません。"),
            ],
        )

    @classmethod
    def execute(cls, model, clip, vae, japanese, english, negative_japanese, negative_english,
                seed, steps, cfg, sampler_name, scheduler, width, height, translation_clip=None):
        return generate(model, clip, vae, japanese, english, negative_japanese, negative_english,
                        seed, steps, cfg, sampler_name, scheduler, translation_clip, None, 1024, width, height)


class QwenImageEdit(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="QwenImageEdit", display_name="Qwen Image 2.1 画像編集",
            category="JP Enhanced/Qwen Image",
            inputs=[io.Image.Input("image", display_name="Image1 編集対象")] + [
                io.Image.Input(f"image_{i}", display_name=f"Image{i} 参照画像（参照要素をプロンプトで明示）", optional=True)
                for i in range(2, 6)
            ] + prompt_inputs() + [
                io.Int.Input("resolution", default=1024, min=0, max=4096, step=32,
                             tooltip="参照画像の面積をresolutionの二乗程度に調整。0で元サイズを32の倍数に調整。出力はimage1の比率。"),
                io.Int.Input("width", display_name="出力幅", optional=True, force_input=True, min=32, max=nodes.MAX_RESOLUTION,
                             tooltip="解像度セレクターのwidthを接続。高さも接続し、multipleは32に設定してください。未接続なら参照画像の比率を使用。"),
                io.Int.Input("height", display_name="出力高さ", optional=True, force_input=True, min=32, max=nodes.MAX_RESOLUTION,
                             tooltip="解像度セレクターのheightを接続。参照画像の解像度はresolutionで別途指定します。"),
            ], outputs=[
                io.Image.Output(),
                io.String.Output("positive_prompt", display_name="最終Positiveプロンプト",
                                 tooltip="翻訳・結合後、生成用CLIPへ渡したテキスト。任意でテキスト表示・保存ノードへ接続できます。"),
                io.String.Output("negative_prompt", display_name="最終Negativeプロンプト",
                                 tooltip="翻訳・結合後のNegativeテキスト。CFG=1でも出力しますが、生成には作用しません。"),
            ],
        )

    @classmethod
    def execute(cls, image, model, clip, vae, japanese, english, negative_japanese, negative_english,
                seed, steps, cfg, sampler_name, scheduler, resolution, translation_clip=None, references=None,
                width=None, height=None, image_2=None, image_3=None, image_4=None, image_5=None):
        if (width is None) != (height is None):
            raise ValueError("出力幅と出力高さは両方接続してください。")
        images = {"image_1": image, **(references or {})}
        images.update({f"image_{i}": ref for i, ref in enumerate((image_2, image_3, image_4, image_5), 2) if ref is not None})
        return generate(model, clip, vae, japanese, english, negative_japanese, negative_english,
                        seed, steps, cfg, sampler_name, scheduler, translation_clip, images, resolution, width, height)

