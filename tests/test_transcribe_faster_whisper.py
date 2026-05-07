import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "transcribe_faster_whisper.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "transcribe_faster_whisper",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ResolveRuntimeConfigTests(unittest.TestCase):
    def test_auto_device_uses_cpu_without_cuda(self):
        module = load_module()
        fake_ct2 = types.SimpleNamespace(
            get_cuda_device_count=lambda: 0,
            get_supported_compute_types=lambda device: ["int8", "float32"],
        )

        config = module.resolve_runtime_config(ctranslate2_module=fake_ct2)

        self.assertEqual(config.device, "cpu")
        self.assertEqual(config.compute_type, "int8")

    def test_auto_device_uses_cuda_when_visible(self):
        module = load_module()
        fake_ct2 = types.SimpleNamespace(
            get_cuda_device_count=lambda: 1,
            get_supported_compute_types=lambda device: ["float16", "int8_float16"],
        )

        config = module.resolve_runtime_config(ctranslate2_module=fake_ct2)

        self.assertEqual(config.device, "cuda")
        self.assertEqual(config.compute_type, "float16")

    def test_unsupported_compute_type_falls_back_to_supported_one(self):
        module = load_module()
        fake_ct2 = types.SimpleNamespace(
            get_cuda_device_count=lambda: 1,
            get_supported_compute_types=lambda device: ["int8_float16", "float32"],
        )

        config = module.resolve_runtime_config(
            device="cuda",
            compute_type="float16",
            ctranslate2_module=fake_ct2,
        )

        self.assertEqual(config.device, "cuda")
        self.assertEqual(config.compute_type, "int8_float16")

    def test_blank_env_values_fall_back_to_defaults(self):
        module = load_module()
        fake_ct2 = types.SimpleNamespace(
            get_cuda_device_count=lambda: 0,
            get_supported_compute_types=lambda device: ["int8", "float32"],
        )

        with patch.dict(
            os.environ,
            {"FW_MODEL_SIZE": "", "FW_DEVICE": "", "FW_COMPUTE_TYPE": ""},
            clear=False,
        ):
            config = module.resolve_runtime_config(ctranslate2_module=fake_ct2)

        self.assertEqual(config.model_size, "small")
        self.assertEqual(config.device, "cpu")
        self.assertEqual(config.compute_type, "int8")


class OutputGenerationTests(unittest.TestCase):
    def test_ms_to_srt_timestamp(self):
        module = load_module()

        self.assertEqual(module.ms_to_srt_timestamp(3723004), "01:02:03,004")

    def test_write_outputs_creates_srt_and_text(self):
        module = load_module()
        segments = [
            types.SimpleNamespace(start=0.0, end=1.25, text="  第一段 "),
            types.SimpleNamespace(start=1.25, end=3.0, text="第二段  "),
        ]

        with TemporaryDirectory() as tmpdir:
            output = module.write_outputs(segments, Path(tmpdir))

            self.assertEqual(output.text_path.read_text(encoding="utf-8"), "第一段 第二段\n")
            self.assertEqual(
                output.srt_path.read_text(encoding="utf-8"),
                "1\n00:00:00,000 --> 00:00:01,250\n第一段\n\n"
                "2\n00:00:01,250 --> 00:00:03,000\n第二段\n\n",
            )

    def test_write_outputs_renumbers_after_skipping_empty_segments(self):
        module = load_module()
        segments = [
            types.SimpleNamespace(start=0.0, end=1.25, text="   "),
            types.SimpleNamespace(start=1.25, end=3.0, text="保留段落"),
        ]

        with TemporaryDirectory() as tmpdir:
            output = module.write_outputs(segments, Path(tmpdir))

            self.assertEqual(
                output.srt_path.read_text(encoding="utf-8"),
                "1\n00:00:01,250 --> 00:00:03,000\n保留段落\n\n",
            )


if __name__ == "__main__":
    unittest.main()
