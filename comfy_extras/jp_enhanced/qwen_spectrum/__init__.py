WEB_DIRECTORY = "web"

import comfy.patcher_extension
from comfy_api.latest import ComfyExtension, io
from .generation import QwenTextToImage, QwenImageEdit
from .spectrum.config import SpectrumConfig
from .spectrum.patcher import create_spectrum_wrapper
from .spectrum.utils import is_qwen_image21_core


class SpectrumGeneration:
    @classmethod
    def define_schema(cls):
        schema = super().define_schema()
        schema.node_id = cls.__name__
        schema.display_name += "（日本語・Spectrum）"
        schema.category = "JP Enhanced/Qwen Image 2.1"
        schema.description = "一部の計算を予測で置き換える近似高速化。細部が変化する可能性があります。無効にして同じseedで比較できます。"
        schema.inputs += [
            io.Boolean.Input("spectrum_enabled", display_name="Spectrum高速化", default=True),
            io.Int.Input("warmup_steps", display_name="最初に実計算するステップ", default=5, min=0, max=64),
            io.Int.Input("tail_actual_steps", display_name="最後に実計算するステップ", default=3, min=0, max=64),
            io.Int.Input("max_forecasts", display_name="連続予測の上限", default=2, min=0, max=32),
            io.Float.Input("flex_window", display_name="予測間隔の増加", default=0.25, min=0, max=8, step=0.05),
            io.Combo.Input("cache_device", display_name="予測履歴の保存先", options=["cpu", "main_device", "offload_device"], default="cpu",
                           tooltip="CPUはVRAMを節約しますが、転送と予測計算が遅くなる場合があります。GPUに余裕があればmain_deviceで比較。"),
        ]
        return schema

    @classmethod
    def execute(cls, model, spectrum_enabled=True, warmup_steps=5, tail_actual_steps=3,
                max_forecasts=2, flex_window=0.25, cache_device="cpu", **kwargs):
        if not spectrum_enabled:
            return super().execute(model=model, **kwargs)
        if not is_qwen_image21_core(model.get_model_object("diffusion_model")):
            raise ValueError("Spectrum高速版にはQwen-Image 2.1モデルを接続してください。")
        config = SpectrumConfig(warmup_steps=warmup_steps, tail_actual_steps=tail_actual_steps,
                                max_consecutive_forecasts=max_forecasts, flex_window=flex_window,
                                cache_device=cache_device)
        config.validate()
        wrapper = create_spectrum_wrapper(config)
        patched = model.clone()
        comfy.patcher_extension.add_wrapper_with_key(
            comfy.patcher_extension.WrappersMP.DIFFUSION_MODEL,
            "jp_qwen_spectrum", wrapper, patched.model_options, is_model_options=True,
        )
        try:
            return super().execute(model=patched, **kwargs)
        finally:
            wrapper.root_state.reset_run()


class JPQwenImage21SpectrumTextToImage(SpectrumGeneration, QwenTextToImage):
    pass


class JPQwenImage21SpectrumImageEdit(SpectrumGeneration, QwenImageEdit):
    pass


class QwenSpectrumExtension(ComfyExtension):
    async def get_node_list(self):
        return [JPQwenImage21SpectrumTextToImage, JPQwenImage21SpectrumImageEdit]


async def comfy_entrypoint():
    return QwenSpectrumExtension()
