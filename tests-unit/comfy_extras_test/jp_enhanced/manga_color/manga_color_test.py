import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
from PIL import Image

import comfy_extras.jp_enhanced.manga_color as module
from comfy_extras.jp_enhanced.manga_color.viggle import ViggleTurboSigmas, run_with_lora


class MangaColorTests(unittest.TestCase):
    def test_multiple_reference_pages_keep_order_and_independent_sizes(self):
        page = torch.zeros(1, 32, 32, 3)
        references = [torch.ones(1, 32, 64, 3), torch.ones(1, 64, 32, 3)]
        latent = {'samples': torch.zeros(1, 16, 2, 2)}
        with patch.object(module.TextEncodeQwenImage21, 'execute', return_value=SimpleNamespace(result=('pos', 'neg', latent))) as encode, \
             patch.object(module.JPMangaColorPhased, 'sample_standard', return_value=latent), \
             patch.object(module.nodes.VAEDecode, 'decode', return_value=(page,)):
            list(module.JPMangaColorPhased().generate_pages(
                [page], 'model', 'clip', 'vae', 'pos', '', 'Standard', 1, 12, 1024, 25, 1.0,
                reference=references[0], additional_references=references[1:]))
        images = encode.call_args.kwargs['images']
        self.assertEqual(list(images), ['image_1', 'image_2', 'image_3'])
        self.assertIs(images['image_1'], page)
        self.assertIs(images['image_2'], references[0])
        self.assertIs(images['image_3'], references[1])

    def test_official_turbo_uses_fixed_schedule_without_extra_lora(self):
        image = torch.ones(1, 32, 32, 3)
        latent = {'samples': torch.zeros(1, 16, 2, 2)}
        with patch.object(module.TextEncodeQwenImage21, 'execute', return_value=SimpleNamespace(result=('pos', 'neg', latent))), \
             patch.object(module.BasicGuider, 'execute', return_value=SimpleNamespace(result=('guider',))), \
             patch.object(module.RandomNoise, 'execute', return_value=SimpleNamespace(result=('noise',))), \
             patch.object(module.SamplerCustomAdvanced, 'execute', return_value=SimpleNamespace(result=(latent,))) as sample, \
             patch.object(module.nodes.VAEDecode, 'decode', return_value=(image,)), \
             patch.object(module.ViggleTurboLora, 'load') as load, \
             patch.object(module.JPMangaColorPhased, 'sample_standard') as standard:
            result = list(module.JPMangaColorPhased().generate_pages(
                [image], 'model', 'clip', 'vae', 'pos', '', 'Official Turbo', 1, 12, 1024, 99, 9.0, image))
        torch.testing.assert_close(sample.call_args.args[3], torch.tensor([
            1.0, 0.978453, 0.95418, 0.926626, 0.89508, 0.845148, 0.704534, 0.414568, 0.0]))
        self.assertIs(result[0], image)
        load.assert_not_called()
        standard.assert_not_called()

    def test_turbo_sequential_positive_only(self):
        node = module.JPMangaColorTurboSequential()
        schema = node.INPUT_TYPES()
        inputs = schema['required'] | schema['optional']
        self.assertIn('positive_english', inputs)
        for name in ('english', 'japanese', 'negative_english', 'negative_japanese',
                     'translation_clip', 'mode', 'steps', 'cfg'):
            self.assertNotIn(name, inputs)
        image = torch.zeros(1, 64, 64, 3)
        result = {'ui': {'images': [{'filename': 'single.png'}]}}
        with patch.object(module.JPMangaColorSequential, 'save_pages', return_value=result) as save:
            actual = node.save_turbo_pages(
                'model', 'clip', 'vae', 'English page corrections', 12, 1280, 'lora',
                'Single image', '', 0, 0, False, 'MangaColor73', single_image=image)
        self.assertIs(actual, result)
        self.assertEqual(save.call_args.args[:11], (
            'model', 'clip', 'vae', 'English page corrections', '', '', '', 'Turbo', 12, 1280, 6))
        self.assertEqual(save.call_args.args[11], 1.0)
        self.assertNotIn('translation_clip', save.call_args.kwargs)
        self.assertIs(save.call_args.kwargs['single_image'], image)

    def test_sequential_save_precedes_next_load_and_survives_error(self):
        events = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('001.png', '002.png'):
                Image.new('RGB', (64, 96)).save(root/name)
            def load(path):
                events.append(('load', path.name))
                return torch.zeros(1, 96, 64, 3)
            def generate(*args):
                events.append(('generate', None))
                if len([e for e in events if e[0] == 'generate']) == 2:
                    raise RuntimeError('second page failed')
                yield args[0][0]
            def save(image, prefix, *args):
                events.append(('save', prefix))
                Image.new('RGB', (image.shape[2], image.shape[1])).save(root/'saved.png')
                return {'ui': {'images': [{'filename': 'saved.png'}]}}
            with patch.object(module, 'load_image', side_effect=load), \
                 patch.object(module.JPMangaColorPhased, 'prepare', return_value=('model','positive','negative')) as prepare, \
                 patch.object(module.JPMangaColorPhased, 'generate_pages', side_effect=generate), \
                 patch.object(module.nodes.SaveImage, 'save_images', side_effect=save):
                with self.assertRaisesRegex(RuntimeError, 'second page'):
                    module.JPMangaColorSequential().save_pages(
                        'model','clip','vae','positive','','negative','', 'Turbo',12,1024,40,2,'lora',
                        'Folder', str(root),0,0,False,'MangaColor13')
            self.assertEqual([e[0] for e in events], ['load','generate','save','load','generate'])
            self.assertTrue((root/'saved.png').exists())
            self.assertEqual(events[2][1], 'MangaColor13/001.png')
            prepare.assert_called_once()

    def test_sequential_single_image_ignores_folder(self):
        node = module.JPMangaColorSequential()
        self.assertEqual(node.check_lazy_status('Folder'), [])
        self.assertEqual(node.check_lazy_status('Single image'), ['single_image'])
        image = torch.zeros(1, 64, 64, 3)
        with patch.object(module, 'image_paths') as paths, \
             patch.object(module.JPMangaColorPhased, 'prepare', return_value=('model','positive','negative')), \
             patch.object(module.JPMangaColorPhased, 'generate_pages', return_value=iter([image])), \
             patch.object(module.nodes.SaveImage, 'save_images', return_value={'ui':{'images':[{'filename':'single.png'}]}}):
            result = node.save_pages('model','clip','vae','positive','','negative','', 'Turbo',12,1024,40,2,'lora',
                'Single image','',0,0,False,'MangaColor13',single_image=image)
        paths.assert_not_called()
        self.assertEqual(result['ui']['images'][0]['filename'], 'single.png')

    def test_phase_order_and_original_sizes(self):
        events = []
        def encode(clip, positive, negative, **kwargs):
            page = kwargs['images']['image_1']
            index = int(page[0, 0, 0, 0])
            events.append(('encode', index))
            return SimpleNamespace(result=(index, -1, {'samples': index}))
        def sample(model, mode, seed, steps, cfg, positive, negative, latent):
            events.append(('sample', positive))
            return latent
        def decode(vae, latent):
            index = latent['samples']
            events.append(('decode', index))
            return (torch.zeros(1, 32, 32, 3),)
        pages = [torch.full((1, 35+i, 45+i, 3), float(i)) for i in range(3)]
        with patch.object(module.TextEncodeQwenImage21, 'execute', side_effect=encode), \
             patch.object(module.JPEnhancedEnglishPrompt, 'execute', return_value=SimpleNamespace(result=['text'])) as translate, \
             patch.object(module.JPMangaColorPhased, 'sample_standard', side_effect=sample), \
             patch.object(module.nodes.VAEDecode, 'decode', side_effect=decode):
            result, = module.JPMangaColorPhased().generate(
                pages, [object()], [object()], [object()], ['prompt'], [''], ['negative'], [''],
                ['Spectrum'], [2], [12], [0], [40], [2.0], ['unused'])
        self.assertEqual(events, [('encode', 0), ('encode', 1), ('sample', 0), ('sample', 1),
                                  ('decode', 0), ('decode', 1), ('encode', 2), ('sample', 2), ('decode', 2)])
        self.assertEqual([tuple(x.shape) for x in result], [tuple(x.shape) for x in pages])
        self.assertEqual(translate.call_count, 2)

    def test_turbo_schedule(self):
        latent = {'samples': torch.empty(1, 64, 78, 52)}
        actual, = ViggleTurboSigmas().get_sigmas(latent, '1,0.9375,0.875,0.75,0.5,0.25')
        mu = .5 + .4 * (78*52-256) / (8192-256)
        expected = [math.exp(mu)/(math.exp(mu)+(1/t-1)) for t in (1,.9375,.875,.75,.5,.25)] + [0]
        torch.testing.assert_close(actual, torch.tensor(expected))

    def test_turbo_uses_reference_and_no_cfg(self):
        reference = torch.zeros(1, 32, 32, 3)
        latent = {'samples': torch.zeros(1, 64, 2, 2)}
        with patch.object(module.TextEncodeQwenImage21, 'execute', return_value=SimpleNamespace(result=('positive', 'negative', latent))) as encode, \
             patch.object(module.JPEnhancedEnglishPrompt, 'execute', return_value=SimpleNamespace(result=['prompt'])) as translate, \
             patch.object(module.ViggleTurboLora, 'load', return_value=('turbo_model',)) as load, \
             patch.object(module.BasicGuider, 'execute', return_value=SimpleNamespace(result=['guider'])) as guider, \
             patch.object(module.SamplerCustomAdvanced, 'execute', return_value=SimpleNamespace(result=[latent])) as sample, \
             patch.object(module.nodes.VAEDecode, 'decode', return_value=(reference,)), \
             patch.object(module.JPMangaColorPhased, 'sample_standard') as standard:
            module.JPMangaColorPhased().generate(
                [reference], ['base'], ['clip'], ['vae'], ['prompt'], [''], ['unused negative'], ['unused'],
                ['Turbo'], [4], [12], [0], [40], [2], ['turbo.safetensors'], reference=[reference])
        translate.assert_called_once()
        load.assert_called_once_with('base', 'turbo.safetensors', 1.0)
        guider.assert_called_once_with('turbo_model', 'positive')
        standard.assert_not_called()
        self.assertEqual(encode.call_args.args[2], '')
        self.assertIs(encode.call_args.kwargs['images']['image_2'], reference)
        self.assertEqual(len(sample.call_args.args[3]), 7)

    def test_fused_mlp_lora_math(self):
        class MLP(torch.nn.Module):
            fused = True
            def __init__(self):
                super().__init__()
                self.gate_up = torch.nn.Linear(3, 8, bias=False)
                self.out = torch.nn.Linear(4, 3, bias=False)
            def forward(self, x):
                g, u = self.gate_up(x).chunk(2, -1)
                return torch.nn.functional.linear(torch.nn.functional.silu(g)*u, self.out.weight)
        model = torch.nn.Sequential(MLP())
        x = torch.randn(2, 3)
        gate = [torch.randn(2, 3), torch.randn(4, 2)]
        up = [torch.randn(2, 3), torch.randn(4, 2)]
        down = [torch.randn(2, 4), torch.randn(3, 2)]
        weights = model[0].gate_up.weight + torch.cat([gate[1]@gate[0], up[1]@up[0]])
        g, u = torch.nn.functional.linear(x, weights).chunk(2, -1)
        expected = torch.nn.functional.linear(torch.nn.functional.silu(g)*u, model[0].out.weight + down[1]@down[0])
        class Executor:
            class_obj = model
            def __call__(self, x): return model(x)
        actual = run_with_lora({'0.gate_layer': gate, '0.proj': up, '0.out': down}, Executor(), x)
        torch.testing.assert_close(actual, expected)
        self.assertFalse(model[0]._forward_hooks)
        self.assertFalse(model[0].gate_up._forward_hooks)

    def test_lora_hook_cleanup_on_failure(self):
        model = torch.nn.Sequential(torch.nn.Linear(3, 2, bias=False))
        before = model[0].weight.detach().clone()
        down = torch.ones(1, 3)
        up = torch.ones(2, 1)
        x = torch.ones(1, 3)
        class Executor:
            class_obj = model
            def __call__(self, x):
                torch.testing.assert_close(model(x), torch.nn.functional.linear(x, before) + 3)
                raise RuntimeError('stop')
        with self.assertRaisesRegex(RuntimeError, 'stop'):
            run_with_lora({'0': [down, up]}, Executor(), x)
        self.assertFalse(model[0]._forward_hooks)
        torch.testing.assert_close(model[0].weight, before)


if __name__ == '__main__':
    unittest.main()
