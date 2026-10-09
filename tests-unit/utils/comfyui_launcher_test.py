import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import psutil

import comfyui_launcher as launcher


class LauncherTests(unittest.TestCase):
    def test_matches_only_this_entry_point(self):
        root = Path.cwd().resolve()
        self.assertTrue(launcher.is_repo_server(['python.exe', 'main.py', '--port', '8188'], root, root))
        self.assertTrue(launcher.is_repo_server(['python.exe', '-u', '-X', 'utf8', str(root/'main.py')], root.parent, root))
        self.assertFalse(launcher.is_repo_server(['python.exe', 'main.py'], root.parent, root))
        self.assertFalse(launcher.is_repo_server(['python.exe', 'other.py', 'main.py'], root, root))
        self.assertFalse(launcher.is_repo_server(['python.exe', '-c', 'main.py'], root, root))
        self.assertFalse(launcher.is_repo_server(['python.exe', '-m', 'main.py'], root, root))

    def test_stops_only_repo_server(self):
        root = Path.cwd().resolve()
        own, other = Mock(pid=1), Mock(pid=2)
        own.cmdline.return_value = ['python.exe', 'main.py']
        own.cwd.return_value = str(root)
        other.cmdline.return_value = ['python.exe', 'main.py']
        other.cwd.return_value = str(root.parent)
        with patch.object(psutil, 'process_iter', return_value=[own, other]), \
             patch.object(psutil, 'wait_procs', return_value=([own], [])), \
             patch.object(psutil, 'net_connections', return_value=[]):
            launcher.stop_existing(root)
        own.terminate.assert_called_once()
        other.terminate.assert_not_called()

    def test_foreign_listener_blocks_start(self):
        connection = SimpleNamespace(status=psutil.CONN_LISTEN, laddr=SimpleNamespace(ip='127.0.0.1', port=8188), pid=42)
        with patch.object(psutil, 'process_iter', return_value=[]), \
             patch.object(psutil, 'wait_procs', return_value=([], [])), \
             patch.object(psutil, 'net_connections', return_value=[connection]):
            with self.assertRaisesRegex(RuntimeError, 'another process'):
                launcher.stop_existing(Path.cwd())

    def test_stop_timeout_blocks_start(self):
        with patch.object(psutil, 'process_iter', return_value=[]), \
             patch.object(psutil, 'wait_procs', return_value=([], [Mock()])):
            with self.assertRaisesRegex(RuntimeError, 'did not stop'):
                launcher.stop_existing(Path.cwd())


if __name__ == '__main__':
    unittest.main()
