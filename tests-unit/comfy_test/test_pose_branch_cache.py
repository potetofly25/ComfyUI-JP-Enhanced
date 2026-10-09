import unittest

import torch

from comfy.ldm.wan.model_animate2 import PoseBranchCache


class PoseBranchCacheTests(unittest.TestCase):
    def test_select_moves_matching_tensor_slot_without_comparing_dicts(self):
        cache = PoseBranchCache()
        first = {"key": torch.tensor([1., 2.]), "blocks": {}}
        second = {"key": torch.tensor([3., 4.]), "blocks": {}}
        cache.slots = [first, second]
        self.assertTrue(cache.select(torch.tensor([3., 4.]), create=False))
        self.assertIs(cache.slot, second)
        self.assertTrue(cache.select(torch.tensor([1., 2.]), create=False))
        self.assertIs(cache.slots[-1], first)
        self.assertIs(cache.slots[0], second)
        self.assertFalse(cache.select(torch.tensor([5., 6.]), create=False))
        self.assertIsNone(cache.slot)
        self.assertEqual(len(cache.slots), 2)
