import unittest
from unittest.mock import Mock, patch

from comfy_api.latest import io
from comfy_extras.jp_enhanced.qwen_spectrum import generation as q
from comfy_extras.nodes_resolution import ResolutionSelector, AspectRatio


class QwenImageTests(unittest.TestCase):
    def test_edit_selector_sets_output_size_without_changing_references(self):
        width, height = ResolutionSelector.execute(AspectRatio.WIDESCREEN_H, 2.0, 32).result
        with patch.object(q.TextEncodeQwenImage21, 'execute', return_value=io.NodeOutput('pos', 'neg', {'samples': 'reference'})) as encode, \
             patch.object(q.nodes.EmptyLatentImage, 'generate', return_value=({'samples': 'selected'},)) as empty, \
             patch.object(q.nodes.KSampler, 'sample', return_value=({},)) as sample, \
             patch.object(q.nodes.VAEDecode, 'decode', return_value=('image',)):
            q.QwenImageEdit.execute('target', 'model', 'clip', 'vae', '', 'edit', '', '',
                                   12, 25, 1, 'euler', 'simple', 1024, width=width, height=height)
            empty.assert_called_once_with(width, height, 1)
            self.assertEqual(encode.call_args.kwargs['images'], {'image_1': 'target'})
            self.assertEqual(encode.call_args.kwargs['resolution'], 1024)
            self.assertEqual(sample.call_args.args[-1], {'samples': 'selected'})

    def test_edit_rejects_partial_size(self):
        with self.assertRaisesRegex(ValueError, '両方接続'):
            q.QwenImageEdit.execute('target', 'model', 'clip', 'vae', '', '', '', '',
                                   12, 25, 1, 'euler', 'simple', 1024, width=1536)

    def test_english_only_generation_routes_dimensions_and_negative(self):
        with patch.object(q.TextEncodeQwenImage21, 'execute', return_value=io.NodeOutput('pos', 'neg', {})) as encode, \
             patch.object(q.nodes.EmptyLatentImage, 'generate', return_value=({'samples': 'empty'},)) as empty, \
             patch.object(q.nodes.KSampler, 'sample', return_value=({'samples': 'result'},)) as sample, \
             patch.object(q.nodes.VAEDecode, 'decode', return_value=('image',)):
            result = q.QwenTextToImage.execute('model', 'clip', 'vae', '', '(detail:1.2)', '', 'blur',
                                                      12, 25, 2, 'euler', 'simple', 1536, 864)
            self.assertEqual(result.result, ('image', '(detail:1.2)', 'blur'))
            self.assertEqual(encode.call_args.args, ('clip', '(detail:1.2)', 'blur'))
            empty.assert_called_once_with(1536, 864, 1)
            self.assertEqual(sample.call_args.args[-1], {'samples': 'empty'})

    def test_edit_keeps_reference_order_and_uses_reference_latent(self):
        translator = Mock()
        translator.decode.side_effect = ['Change <image1> using <image2>.', 'unwanted text']
        with patch.object(q.TextEncodeQwenImage21, 'execute', return_value=io.NodeOutput('pos', 'neg', {'samples': 'reference'})) as encode, \
             patch.object(q.nodes.EmptyLatentImage, 'generate') as empty, \
             patch.object(q.nodes.KSampler, 'sample', return_value=({},)) as sample, \
             patch.object(q.nodes.VAEDecode, 'decode', return_value=('image',)):
            result = q.QwenImageEdit.execute('target', 'model', 'clip', 'vae', '服を変更', 'natural light', '不要な文字', 'watermark',
                                            12, 25, 1, 'euler', 'simple', 0, translator, {'image_2': 'shirt'})
            self.assertEqual(encode.call_args.kwargs['images'], {'image_1': 'target', 'image_2': 'shirt'})
            self.assertEqual(encode.call_args.kwargs['resolution'], 0)
            self.assertEqual(sample.call_args.args[-1], {'samples': 'reference'})
            empty.assert_not_called()
            self.assertEqual(result.result[0], 'image')
            self.assertEqual(result.result[1:], encode.call_args.args[1:3])
            self.assertIn('Change <image1> using <image2>.', result.result[1])
            self.assertIn('natural light', result.result[1])
            self.assertIn('unwanted text', result.result[2])
            self.assertIn('watermark', result.result[2])


if __name__ == '__main__':
    unittest.main()
