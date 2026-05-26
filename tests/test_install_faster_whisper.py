import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "install_faster_whisper.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "install_faster_whisper",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class InstallFasterWhisperTests(unittest.TestCase):
    def test_select_fastest_mirror_ignores_failed_probes(self):
        module = load_module()
        mirrors = [
            module.PyPIMirror("slow", "https://slow.example/simple", None),
            module.PyPIMirror("fast", "https://fast.example/simple", None),
            module.PyPIMirror("down", "https://down.example/simple", None),
        ]

        def probe(mirror, timeout):
            if mirror.name == "down":
                return None
            return 1.2 if mirror.name == "slow" else 0.2

        selected = module.select_fastest_mirror(mirrors, probe=probe, timeout=1)

        self.assertEqual(selected.name, "fast")

    def test_build_install_command_uses_selected_mirror_and_venv_python(self):
        module = load_module()
        mirror = module.PyPIMirror(
            "清华",
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "pypi.tuna.tsinghua.edu.cn",
        )

        command = module.build_install_command(
            Path("/tmp/fw-venv/bin/python"),
            mirror,
        )

        self.assertEqual(command[0], "/tmp/fw-venv/bin/python")
        self.assertIn("-i", command)
        self.assertIn("https://pypi.tuna.tsinghua.edu.cn/simple", command)
        self.assertIn("--trusted-host", command)
        self.assertIn("pypi.tuna.tsinghua.edu.cn", command)
        self.assertEqual(command[-2:], ["pip", "faster-whisper"])


if __name__ == "__main__":
    unittest.main()
