import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "download_video_candidates.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "download_video_candidates",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size=-1):
        if self.body == b"":
            return b""
        if size == -1:
            chunk, self.body = self.body, b""
            return chunk
        chunk, self.body = self.body[:size], self.body[size:]
        return chunk


class CandidateDownloadTests(unittest.TestCase):
    def test_extract_candidates_prefers_download_urls_and_dedupes(self):
        module = load_module()
        response = {
            "download_url": "https://cdn.example/a.mp4",
            "download_urls": [
                "https://cdn.example/a.mp4",
                "https://cdn.example/b.mp4",
                "https://cdn.example/a.mp4",
            ],
        }

        candidates = module.extract_candidates(response)

        self.assertEqual(
            candidates,
            ["https://cdn.example/a.mp4", "https://cdn.example/b.mp4"],
        )

    def test_download_tries_next_candidate_when_first_fails(self):
        module = load_module()
        attempts = []

        def opener(request, timeout):
            attempts.append(request.full_url)
            if request.full_url == "https://cdn.example/bad.mp4":
                raise OSError("network stalled")
            return FakeResponse(b"video-bytes")

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "video.mp4"
            result = module.download_first_working_candidate(
                ["https://cdn.example/bad.mp4", "https://cdn.example/good.mp4"],
                output_path,
                opener=opener,
                timeout=1,
            )

            self.assertEqual(result, "https://cdn.example/good.mp4")
            self.assertEqual(attempts, ["https://cdn.example/bad.mp4", "https://cdn.example/good.mp4"])
            self.assertEqual(output_path.read_bytes(), b"video-bytes")

    def test_download_logs_redacted_candidate_not_full_signed_url(self):
        module = load_module()
        signed_url = "https://cdn.example/video.mp4?secret=token"

        with TemporaryDirectory() as tmpdir:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                result = module.download_first_working_candidate(
                    [signed_url],
                    Path(tmpdir) / "video.mp4",
                    opener=lambda request, timeout: FakeResponse(b"video-bytes"),
                    timeout=1,
                )

        self.assertEqual(result, signed_url)
        self.assertIn("cdn.example.mp4", stderr.getvalue())
        self.assertNotIn("secret=token", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
