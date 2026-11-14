import unittest
from backend import orbit


class OrbitPropagationTests(unittest.TestCase):
    def test_tle_loaded(self):
        tle = orbit.fetch_latest_tle()
        self.assertIn("MEAN_MOTION", tle)
        self.assertIn("INCLINATION", tle)
        self.assertEqual(tle.get("NORAD_CAT_ID", 63182), 63182)

    def test_propagate_orbit_returns_valid_telemetry(self):
        pos = orbit.propagate_orbit()
        self.assertIn("latitude", pos)
        self.assertIn("longitude", pos)
        self.assertIn("altitude_km", pos)
        self.assertIn("velocity_kms", pos)
        self.assertIn("in_sunlight", pos)

        # SPHEREx Sun-Synchronous LEO orbit checks
        self.assertGreaterEqual(pos["latitude"], -90.0)
        self.assertLessEqual(pos["latitude"], 90.0)
        self.assertGreaterEqual(pos["longitude"], -180.0)
        self.assertLessEqual(pos["longitude"], 180.0)
        self.assertGreater(pos["altitude_km"], 600.0)
        self.assertLess(pos["altitude_km"], 800.0)
        self.assertGreater(pos["velocity_kms"], 7.0)
        self.assertLess(pos["velocity_kms"], 8.0)

    def test_ground_track_generates_points(self):
        track = orbit.generate_ground_track(start_offset_minutes=-10, end_offset_minutes=10, step_minutes=2)
        self.assertEqual(len(track), 11)
        self.assertTrue(any(p["is_current"] for p in track))


if __name__ == "__main__":
    unittest.main()
