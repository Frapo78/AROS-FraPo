"""Focused tests with a fake local HMP endpoint; no QEMU guest is booted."""

import importlib.util
from pathlib import Path
import socket
import tempfile
import threading
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("screen_capture", HERE / "capture-qemu-screen.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CaptureTests(unittest.TestCase):
    def test_missing_socket_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertFalse(module.capture(temp + "/missing.sock", temp + "/screen.ppm"))

    def test_unsafe_path_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertFalse(module.capture(temp + "/missing.sock", temp + '/screen";quit.ppm'))

    def test_refuses_existing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            screenshot = Path(temp) / "screen.ppm"
            screenshot.write_bytes(b"P6")
            self.assertFalse(module.capture(temp + "/missing.sock", str(screenshot)))

    def test_synthetic_ppm_and_spoofed_payload(self):
        for payload, expected in ((b"P6\\n1 1\\n255\\n\\x00\\x00\\x00", True), (b"FAKE", False)):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as temp:
                path = Path(temp)
                endpoint = str(path / "monitor.sock")
                output = str(path / "screen.ppm")
                ready = threading.Event()
                def server():
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                        sock.bind(endpoint)
                        sock.listen(1)
                        ready.set()
                        peer, _ = sock.accept()
                        with peer:
                            command = peer.recv(4096)
                            if command == f"screendump {output}\\n".encode("ascii"):
                                Path(output).write_bytes(payload)
                t = threading.Thread(target=server, daemon=True)
                t.start()
                self.assertTrue(ready.wait(2))
                self.assertEqual(module.capture(endpoint, output), expected)
                t.join(2)
                self.assertFalse(t.is_alive())


if __name__ == "__main__":
    unittest.main()
