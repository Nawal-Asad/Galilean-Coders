import unittest
from unittest.mock import patch

from frontend.app import app


class FrontendRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_landing_page_links_to_data_explorer(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/explorer"', response.data)

    def test_data_explorer_contains_filters_and_candidate_detail(self):
        response = self.client.get("/explorer")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Minimum |significance|", response.data)
        self.assertIn(b"candidate-dialog", response.data)
        self.assertIn(b"/api/cutout", response.data)
        self.assertIn(b"noise model still needs scientific calibration", response.data)
        self.assertIn(b"epoch2_aligned_to_epoch1.fits", response.data)
        self.assertIn(b"epoch2_minus_epoch1_difference.fits", response.data)
        self.assertIn(b"candidate-overlay", response.data)
        self.assertIn(b"exact pixel position", response.data)

    def test_tracker_page_loads(self):
        response = self.client.get("/tracker")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Live Satellite Tracker", response.data)
        self.assertIn(b"groundtrack-canvas", response.data)
        self.assertIn(b"/static/geo_location.js", response.data)

    def test_tracker_geography_datasets_are_local(self):
        countries = self.client.get("/geography/ne_50m_admin_0_countries.geojson")
        oceans = self.client.get("/geography/ne_50m_geography_marine_polys.geojson")
        self.assertEqual(countries.status_code, 200)
        self.assertEqual(oceans.status_code, 200)
        self.assertIn(b'"FeatureCollection"', countries.data)
        self.assertIn(b'"FeatureCollection"', oceans.data)

    def test_tracker_rejects_unknown_geography_dataset(self):
        response = self.client.get("/geography/not-allowed.geojson")
        self.assertEqual(response.status_code, 404)

    def test_fits_viewer_page_loads(self):
        response = self.client.get("/fits")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FITS Image & Header Viewer", response.data)
        self.assertIn(b"fits-file-select", response.data)

    def test_api_pages_use_configured_backend_url(self):
        with patch("frontend.app.API_BASE_URL", "https://api.example.com/"):
            for path in ("/explorer", "/fits", "/tracker"):
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(
                        b'https://api.example.com',
                        response.data,
                    )


if __name__ == "__main__":
    unittest.main()
