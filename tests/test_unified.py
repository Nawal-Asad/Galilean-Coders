import asyncio
import unittest

from unified_app import app


class UnifiedAppTests(unittest.TestCase):
    def fetch(self, path: str):
        """Invoke the unified ASGI application in-memory."""
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [(b"host", b"localhost")],
        }
        status_code = None
        headers = []
        body_parts = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            nonlocal status_code, headers, body_parts
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

        async def run():
            await app(scope, receive, send)

        asyncio.run(run())
        body = b"".join(body_parts).decode("utf-8", errors="replace")
        return status_code, dict(headers), body

    def test_root_serves_landing_page(self):
        status, headers, body = self.fetch("/")
        self.assertEqual(status, 200)
        self.assertIn("SPHEREx", body)
        self.assertIn("102 colors", body)

    def test_explorer_route_serves_data_explorer(self):
        status, headers, body = self.fetch("/explorer")
        self.assertEqual(status, 200)
        self.assertIn("Data Explorer", body)
        self.assertIn("candidate-dialog", body)

    def test_tracker_route_serves_satellite_tracker(self):
        status, headers, body = self.fetch("/tracker")
        self.assertEqual(status, 200)
        self.assertIn("Live Satellite Tracker", body)
        self.assertIn("groundtrack-canvas", body)

    def test_fits_route_serves_fits_viewer(self):
        status, headers, body = self.fetch("/fits")
        self.assertEqual(status, 200)
        self.assertIn("FITS Image & Header Viewer", body)
        self.assertIn("fits-file-select", body)

    def test_api_status_endpoint(self):
        status, headers, body = self.fetch("/api")
        self.assertEqual(status, 200)
        self.assertIn("SPHEREx Sky Explorer backend API is running", body)

    def test_api_docs_available(self):
        status, headers, body = self.fetch("/docs")
        self.assertEqual(status, 200)
        self.assertIn("swagger", body.lower())

    def test_routes_registered_on_unified_app(self):
        paths = [getattr(route, "path", None) for route in app.routes]
        self.assertIn("/api", paths)
        self.assertIn("/api/compare", paths)
        self.assertIn("/api/candidates", paths)
        self.assertIn("/api/cutout", paths)
        self.assertIn("/api/orbit/telemetry", paths)
        self.assertIn("/api/orbit/groundtrack", paths)
        self.assertIn("/api/fits/files", paths)
        self.assertIn("/api/fits/info", paths)
        self.assertIn("/api/fits/image", paths)
        self.assertIn("/docs", paths)


if __name__ == "__main__":
    unittest.main()
