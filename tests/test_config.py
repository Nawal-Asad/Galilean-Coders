import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


class EnvironmentConfigTests(unittest.TestCase):
    def test_environment_overrides_server_and_storage_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory) / "observations"
            results_dir = Path(directory) / "catalogues"
            environment = os.environ.copy()
            environment.update({
                "HOST": "0.0.0.0",
                "PORT": "9123",
                "SPHEREX_DATA_DIR": str(data_dir),
                "SPHEREX_RESULTS_DIR": str(results_dir),
                "SPHEREX_CORS_ORIGINS": "https://example.com, https://www.example.com",
            })
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import json; from spherex import config; "
                        "print(json.dumps({"
                        "'host': config.HOST, 'port': config.PORT, "
                        "'data_dir': str(config.DATA_DIR), "
                        "'results_dir': str(config.RESULTS_DIR), "
                        "'origins': config.CORS_ORIGINS}))"
                    ),
                ],
                check=True,
                capture_output=True,
                cwd=PROJECT_DIR,
                env=environment,
                text=True,
            )

        settings = json.loads(result.stdout)
        self.assertEqual(settings["host"], "0.0.0.0")
        self.assertEqual(settings["port"], 9123)
        self.assertEqual(settings["data_dir"], str(data_dir))
        self.assertEqual(settings["results_dir"], str(results_dir))
        self.assertEqual(
            settings["origins"],
            ["https://example.com", "https://www.example.com"],
        )

    def test_invalid_port_fails_with_configuration_error(self):
        environment = os.environ.copy()
        environment["PORT"] = "not-a-port"
        result = subprocess.run(
            [sys.executable, "-c", "import spherex.config"],
            capture_output=True,
            cwd=PROJECT_DIR,
            env=environment,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PORT must be an integer", result.stderr)


if __name__ == "__main__":
    unittest.main()
