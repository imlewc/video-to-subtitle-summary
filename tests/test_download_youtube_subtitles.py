import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "download_youtube_subtitles.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "download_youtube_subtitles",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class YoutubeSubtitleTests(unittest.TestCase):
    def test_build_ytdlp_command_prefers_subtitles_without_video(self):
        module = load_module()

        command = module.build_ytdlp_command(
            url="https://www.youtube.com/watch?v=O87FdYIPeQk",
            output_stem=Path("/tmp/video_analysis/O87FdYIPeQk/subtitle"),
            languages=["zh-Hans", "zh", "en"],
        )

        self.assertIn("--skip-download", command)
        self.assertIn("--ignore-config", command)
        self.assertIn("--ignore-no-formats-error", command)
        self.assertIn("--write-subs", command)
        self.assertIn("--write-auto-subs", command)
        self.assertIn("--sub-langs", command)
        self.assertIn("zh-Hans,zh,en", command)

    def test_convert_vtt_writes_srt_and_plain_text(self):
        module = load_module()
        vtt = """WEBVTT

00:00:00.000 --> 00:00:01.250
Hello <c>world</c>

00:00:01.250 --> 00:00:03.000
第二段
"""

        with TemporaryDirectory() as tmpdir:
            output = module.convert_vtt_to_outputs(vtt, Path(tmpdir))

            self.assertEqual(
                output.srt_path.read_text(encoding="utf-8"),
                "1\n00:00:00,000 --> 00:00:01,250\nHello world\n\n"
                "2\n00:00:01,250 --> 00:00:03,000\n第二段\n\n",
            )
            self.assertEqual(
                output.text_path.read_text(encoding="utf-8"),
                "Hello world 第二段\n",
            )


if __name__ == "__main__":
    unittest.main()
