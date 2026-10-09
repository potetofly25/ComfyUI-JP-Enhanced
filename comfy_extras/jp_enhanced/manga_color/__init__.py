from pathlib import Path

import nodes

from comfy_extras.jp_enhanced.prompt import JPEnhancedEnglishPrompt
from comfy_extras.jp_enhanced.image_input import image_paths, load_image
from comfy_extras.jp_enhanced.qwen_spectrum.generation import EDIT_RULES, NEGATIVE_RULES
from comfy_extras.jp_enhanced.qwen_spectrum.spectrum.config import SpectrumConfig
from comfy_extras.jp_enhanced.qwen_spectrum.spectrum.patcher import create_spectrum_wrapper
from comfy_extras.nodes_custom_sampler import BasicGuider, RandomNoise, SamplerCustomAdvanced
from comfy_extras.nodes_qwen import TextEncodeQwenImage21
import comfy.patcher_extension
import comfy.samplers
import comfy.model_management
import folder_paths

from .viggle import ViggleTurboLora, ViggleTurboSigmas


class JPMangaColorPhased:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image": ("IMAGE",),
            "model": ("MODEL",), "clip": ("CLIP",), "vae": ("VAE",),
            "english": ("STRING", {"forceInput": True}),
            "japanese": ("STRING", {"forceInput": True}),
            "negative_english": ("STRING", {"forceInput": True}),
            "negative_japanese": ("STRING", {"forceInput": True}),
            "mode": (["Spectrum", "Turbo", "Standard"],),
            "pages_per_group": ("INT", {"default": 4, "min": 1, "max": 32}),
            "seed": ("INT", {"default": 12, "min": 0, "max": 0xffffffffffffffff}),
            "resolution": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 32}),
            "steps": ("INT", {"default": 40, "min": 1, "max": 10000}),
            "cfg": ("FLOAT", {"default": 2.0, "min": 0, "max": 100}),
            "lora_name": (folder_paths.get_filename_list("loras"),),
        }, "optional": {"reference": ("IMAGE",), "translation_clip": ("CLIP",)}}

    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True,)
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "JP Enhanced/Manga Color"

    def generate(self, image, model, clip, vae, english, japanese, negative_english,
                 negative_japanese, mode, pages_per_group, seed, resolution, steps, cfg,
                 lora_name, reference=None, translation_clip=None):
        model, clip, vae = model[0], clip[0], vae[0]
        mode = mode[0]
        translator = translation_clip[0] if translation_clip else None
        model, positive, negative = self.prepare(model, mode, japanese[0], english[0],
            negative_japanese[0], negative_english[0], translator, lora_name[0])
        return (list(self.generate_pages(image, model, clip, vae, positive, negative, mode,
            pages_per_group[0], seed[0], resolution[0], steps[0], cfg[0], reference[0] if reference else None)),)

    @staticmethod
    def prepare(model, mode, japanese, english, negative_japanese, negative_english, translator, lora_name):
        positive = JPEnhancedEnglishPrompt.execute(
            clip=translator, texts={"text_0": japanese}, translation_rules=EDIT_RULES,
            english_suffix=english).result[0]
        negative = ""
        if mode != "Turbo":
            negative = JPEnhancedEnglishPrompt.execute(
                clip=translator, texts={"text_0": negative_japanese}, translation_rules=NEGATIVE_RULES,
                english_suffix=negative_english).result[0]
        if mode == "Turbo":
            model = ViggleTurboLora().load(model, lora_name, 1.0)[0]
        return model, positive, negative

    def generate_pages(self, image, model, clip, vae, positive, negative, mode,
                       pages_per_group, seed, resolution, steps, cfg, reference=None):
        for start in range(0, len(image), pages_per_group):
            pages = image[start:start + pages_per_group]
            encoded = []
            for page in pages:
                images = {"image_1": page}
                if reference is not None:
                    images["image_2"] = reference
                encoded.append(TextEncodeQwenImage21.execute(
                    clip, positive, negative, vae=vae, resolution=resolution, images=images).result)
            sampled = []
            for conditioning, unconditioned, latent in encoded:
                if mode == "Turbo":
                    sigmas = ViggleTurboSigmas().get_sigmas(latent, "1.0, 0.9375, 0.875, 0.75, 0.5, 0.25")[0]
                    sampled.append(SamplerCustomAdvanced.execute(
                        RandomNoise.execute(seed).result[0],
                        BasicGuider.execute(model, conditioning).result[0],
                        comfy.samplers.sampler_object("euler"), sigmas, latent).result[0])
                else:
                    sampled.append(self.sample_standard(model, mode, seed, steps, cfg, conditioning, unconditioned, latent))
            del encoded
            for page, latent in zip(pages, sampled):
                decoded = nodes.VAEDecode().decode(vae, latent)[0]
                height, width = page.shape[1:3]
                if decoded.shape[1:3] != (height, width):
                    decoded = nodes.ImageScale().upscale(decoded, "lanczos", width, height, "disabled")[0]
                yield decoded

    @staticmethod
    def sample_standard(model, mode, seed, steps, cfg, positive, negative, latent):
        wrapper = None
        if mode == "Spectrum":
            model = model.clone()
            wrapper = create_spectrum_wrapper(SpectrumConfig(
                warmup_steps=5, tail_actual_steps=3, max_consecutive_forecasts=2,
                flex_window=0.25, cache_device="cpu"))
            comfy.patcher_extension.add_wrapper_with_key(
                comfy.patcher_extension.WrappersMP.DIFFUSION_MODEL,
                "jp_manga_spectrum", wrapper, model.model_options, is_model_options=True)
        try:
            return nodes.KSampler().sample(model, seed, steps, cfg, "euler", "simple", positive, negative, latent)[0]
        finally:
            if wrapper is not None:
                wrapper.root_state.reset_run()


class JPMangaColorSequential:
    @classmethod
    def INPUT_TYPES(cls):
        schema = JPMangaColorPhased.INPUT_TYPES()
        schema['required'].pop('image')
        schema['required'].pop('pages_per_group')
        schema['required'].update({
            'source': (['Folder', 'Single image'],),
            'folder': ('STRING', {'default': '', 'forceInput': True}),
            'image_load_cap': ('INT', {'default': 0, 'min': 0}),
            'start_index': ('INT', {'default': 0, 'min': 0}),
            'include_subfolders': ('BOOLEAN', {'default': False}),
            'filename_prefix': ('STRING', {'default': 'MangaColor13'}),
        })
        schema['optional']['single_image'] = ('IMAGE', {'lazy': True})
        schema['hidden'] = {'prompt': 'PROMPT', 'extra_pnginfo': 'EXTRA_PNGINFO'}
        return schema

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = 'save_pages'
    CATEGORY = 'JP Enhanced/Manga Color'

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float('nan')

    def check_lazy_status(self, source, single_image=None, **kwargs):
        return ['single_image'] if source == 'Single image' and single_image is None else []

    def save_pages(self, model, clip, vae, english, japanese, negative_english, negative_japanese,
                   mode, seed, resolution, steps, cfg, lora_name, source, folder, image_load_cap,
                   start_index, include_subfolders, filename_prefix, reference=None, translation_clip=None,
                   single_image=None, prompt=None, extra_pnginfo=None):
        paths = image_paths(folder, image_load_cap, start_index, include_subfolders) if source == 'Folder' else [None]
        engine = JPMangaColorPhased()
        model, positive, negative = engine.prepare(model, mode, japanese, english,
            negative_japanese, negative_english, translation_clip, lora_name)
        saved = []
        saver = nodes.SaveImage()
        for path in paths:
            comfy.model_management.throw_exception_if_processing_interrupted()
            page = load_image(path) if path is not None else single_image
            name = path.relative_to(Path(folder)).as_posix() if path is not None else 'single'
            # Keep the source extension in the prefix to distinguish page.jpg and page.png.
            prefix = filename_prefix.rstrip('/\\') + '/' + name
            for result in engine.generate_pages([page], model, clip, vae, positive, negative,
                    mode, 1, seed, resolution, steps, cfg, reference):
                saved.extend(saver.save_images(result, prefix, prompt, extra_pnginfo)['ui']['images'])
            del page, result
        return {'ui': {'images': saved}}


class JPMangaColorTurboSequential(JPMangaColorSequential):
    @classmethod
    def INPUT_TYPES(cls):
        schema = super().INPUT_TYPES()
        required = schema['required']
        schema['required'] = {
            ('positive_english' if name == 'english' else name): spec
            for name, spec in required.items()
            if name not in ('japanese', 'negative_english', 'negative_japanese', 'mode', 'steps', 'cfg')
        }
        schema['optional'].pop('translation_clip')
        return schema

    FUNCTION = 'save_turbo_pages'

    def save_turbo_pages(self, model, clip, vae, positive_english, seed, resolution, lora_name,
                        source, folder, image_load_cap, start_index, include_subfolders,
                        filename_prefix, reference=None, single_image=None, prompt=None, extra_pnginfo=None):
        return super().save_pages(
            model, clip, vae, positive_english, '', '', '', 'Turbo', seed, resolution, 6, 1.0,
            lora_name, source, folder, image_load_cap, start_index, include_subfolders,
            filename_prefix, reference=reference, single_image=single_image,
            prompt=prompt, extra_pnginfo=extra_pnginfo)


NODE_CLASS_MAPPINGS = {
    'JPMangaColorPhased': JPMangaColorPhased,
    'JPMangaColorSequential': JPMangaColorSequential,
    'JPMangaColorTurboSequential': JPMangaColorTurboSequential,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    'JPMangaColorPhased': '漫画カラー化（工程別・Spectrum／Turbo）',
    'JPMangaColorSequential': '漫画カラー化（1枚ずつ読込・生成・保存）',
    'JPMangaColorTurboSequential': '漫画カラー化（Turbo・英語Positive・1枚ずつ保存）',
}
