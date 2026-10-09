import unittest
from unittest.mock import Mock, patch
from comfy_api.latest import io
from comfy_extras.jp_enhanced import qwen_spectrum as q
from comfy_extras.jp_enhanced.qwen_spectrum.generation import QwenTextToImage


class NodeLifetimeTest(unittest.TestCase):
    def test_disabled_uses_original_model(self):
        model = Mock()
        with patch.object(QwenTextToImage, 'execute', return_value=io.NodeOutput('image')) as run:
            result = q.JPQwenImage21SpectrumTextToImage.execute(model=model, spectrum_enabled=False)
            run.assert_called_once_with(model=model)
            model.clone.assert_not_called()
            self.assertEqual(result.result, ('image',))

    def test_history_is_released_after_success_and_failure(self):
        for fails in [False, True]:
            model = Mock()
            model.clone.return_value.model_options = {}
            wrapper = Mock()
            with patch.object(q, 'is_qwen_image21_core', return_value=True), \
                 patch.object(q, 'create_spectrum_wrapper', return_value=wrapper), \
                 patch.object(QwenTextToImage, 'execute', side_effect=RuntimeError('stop') if fails else None, return_value=io.NodeOutput('image')) as run:
                if fails:
                    with self.assertRaisesRegex(RuntimeError, 'stop'):
                        q.JPQwenImage21SpectrumTextToImage.execute(model=model)
                else:
                    q.JPQwenImage21SpectrumTextToImage.execute(model=model)
                self.assertIs(run.call_args.kwargs['model'], model.clone.return_value)
                wrapper.root_state.reset_run.assert_called_once()
