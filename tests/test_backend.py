import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from astropy.io import fits
from fastapi import HTTPException
from PIL import Image

from backend import main, processing
from scripts import improve_candidate_detection


class CompareEpochsTests(unittest.TestCase):
    def test_comparison_ignores_non_finite_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory)
            raw_dir = project_dir / "raw"
            processed_dir = project_dir / "processed"
            raw_dir.mkdir()
            processed_dir.mkdir()
            image1 = np.array([[1, 2], [np.nan, 4]], dtype=np.float32)
            image2 = np.array([[3, 5], [6, 9]], dtype=np.float32)
            image_hdu = fits.ImageHDU(image1, name="IMAGE")
            image_hdu.header["BUNIT"] = "test-unit"
            fits.HDUList([
                fits.PrimaryHDU(),
                image_hdu,
            ]).writeto(raw_dir / "epoch1.fits")
            fits.PrimaryHDU(image2).writeto(processed_dir / "epoch2_aligned_to_epoch1.fits")

            with patch.object(
                processing,
                "get_data_path",
                side_effect=lambda name, processed=False: (
                    (processed_dir if processed else raw_dir) / name
                ),
            ):
                result = processing.compare_epochs()

        self.assertEqual(result["valid_pixels"], 3)
        self.assertAlmostEqual(result["mean_difference"], 10 / 3, places=6)
        self.assertEqual(result["median_difference"], 3.0)
        self.assertEqual(result["difference_unit"], "test-unit")

    def test_comparison_rejects_all_invalid_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory)
            raw_dir = project_dir / "raw"
            processed_dir = project_dir / "processed"
            raw_dir.mkdir()
            processed_dir.mkdir()
            image = np.full((2, 2), np.nan, dtype=np.float32)
            fits.HDUList([
                fits.PrimaryHDU(),
                fits.ImageHDU(image, name="IMAGE"),
            ]).writeto(raw_dir / "epoch1.fits")
            fits.PrimaryHDU(image).writeto(processed_dir / "epoch2_aligned_to_epoch1.fits")

            with patch.object(
                processing,
                "get_data_path",
                side_effect=lambda name, processed=False: (
                    (processed_dir if processed else raw_dir) / name
                ),
            ):
                with self.assertRaisesRegex(ValueError, "No finite pixels"):
                    processing.compare_epochs()


class CandidateApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.candidates_file = self.project_dir / "candidates.csv"
        self.difference_file = self.project_dir / "difference.fits"
        main._load_candidates.cache_clear()

    def tearDown(self):
        main._load_candidates.cache_clear()
        self.temporary_directory.cleanup()

    def write_candidates(self, csv_text):
        self.candidates_file.write_text(csv_text, encoding="utf-8")

    def test_candidate_api_normalizes_schema_filters_and_sorts(self):
        self.write_candidates(
            "x,y,difference,significance,type\n"
            "4,5,0.2,6,positive\n"
            "8,9,-0.4,-12,negative\n"
            "10,11,0.1,8,positive\n"
        )
        with patch.object(main, "CANDIDATES_FILE", self.candidates_file):
            result = main.get_candidates(
                limit=10,
                offset=0,
                candidate_type="positive",
                min_abs_significance=7,
                sort_by="significance",
            )

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["candidates"][0]["x"], 10)
        self.assertEqual(result["candidates"][0]["significance"], 8)
        self.assertFalse(result["results_are_validated_detections"])

    def test_api_uses_the_canonical_detector_output(self):
        self.assertEqual(main.CANDIDATES_FILE.name, "candidate_sources.csv")

    def test_candidate_api_reads_legacy_column_names(self):
        self.write_candidates(
            "type,x_pixel,y_pixel,difference,significance_sigma\n"
            "negative,3,7,-0.3,-9.5\n"
        )
        with patch.object(main, "CANDIDATES_FILE", self.candidates_file):
            result = main.get_candidates(
                limit=10,
                offset=0,
                min_abs_significance=None,
                sort_by="file",
            )

        self.assertEqual(
            result["candidates"],
            [{
                "x": 3,
                "y": 7,
                "difference": -0.3,
                "significance": -9.5,
                "type": "negative",
            }],
        )

    def test_candidate_api_rejects_invalid_csv_rows(self):
        self.write_candidates(
            "x,y,difference,significance,type\n"
            "not-a-pixel,5,0.2,6,positive\n"
        )
        with patch.object(main, "CANDIDATES_FILE", self.candidates_file):
            with self.assertRaises(HTTPException) as error:
                main.get_candidates(limit=10, offset=0)

        self.assertEqual(error.exception.status_code, 500)

    def test_cutout_returns_bounded_patch_and_rejects_out_of_range(self):
        image = np.arange(100, dtype=np.float32).reshape(10, 10)
        image[0, 0] = np.nan
        fits.PrimaryHDU(image).writeto(self.difference_file)
        with patch.object(main, "DIFFERENCE_FILE", self.difference_file):
            result = main.get_candidate_cutout(x=0, y=0, radius=2)
            with self.assertRaises(HTTPException) as error:
                main.get_candidate_cutout(x=10, y=0, radius=2)

        self.assertEqual(len(result["difference"]), 3)
        self.assertEqual(len(result["difference"][0]), 3)
        self.assertIsNone(result["difference"][0][0])
        self.assertEqual(error.exception.status_code, 400)

    def test_fits_image_rendering_preserves_pixel_aspect_ratio(self):
        image_file = self.project_dir / "image.fits"
        fits.PrimaryHDU(np.arange(15, dtype=np.float32).reshape(3, 5)).writeto(image_file)
        with patch.object(main, "_resolve_fits", return_value=image_file):
            response = main.render_fits_image(
                file="test.fits",
                hdu="auto",
                percentile_low=1.0,
                percentile_high=99.5,
                colormap="inferno",
            )

        with Image.open(io.BytesIO(response.body)) as rendered:
            self.assertEqual(rendered.size, (1200, 720))


class CandidateDetectionTests(unittest.TestCase):
    def test_detector_writes_the_api_schema_and_excludes_invalid_peaks(self):
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory)
            shape = (11, 11)
            image1 = np.zeros(shape, dtype=np.float32)
            image2 = np.zeros(shape, dtype=np.float32)
            image2[5, 5] = 15
            image2[2, 2] = -15
            variance = np.ones(shape, dtype=np.float32)
            flags = np.zeros(shape, dtype=np.int32)
            aligned_flags = flags.copy()
            aligned_flags[0, 0] = -1
            footprint = np.ones(shape, dtype=np.float32)
            footprint[0, 0] = 0

            fits.HDUList([
                fits.PrimaryHDU(),
                fits.ImageHDU(image1, name="IMAGE"),
                fits.ImageHDU(flags, name="FLAGS"),
                fits.ImageHDU(variance, name="VARIANCE"),
            ]).writeto(project_dir / "epoch1.fits")
            fits.PrimaryHDU(image2).writeto(project_dir / "epoch2_aligned_to_epoch1.fits")
            fits.PrimaryHDU(variance).writeto(project_dir / "epoch2_variance_aligned.fits")
            fits.PrimaryHDU(aligned_flags).writeto(project_dir / "epoch2_flags_aligned.fits")
            fits.PrimaryHDU(footprint).writeto(project_dir / "epoch2_alignment_footprint.fits")
            output_file = project_dir / "candidate_sources.csv"

            raw_dir = project_dir / "raw"
            processed_dir = project_dir / "processed"
            raw_dir.mkdir()
            processed_dir.mkdir()
            for name in ("epoch1.fits",):
                (project_dir / name).replace(raw_dir / name)
            for name in (
                "epoch2_aligned_to_epoch1.fits",
                "epoch2_variance_aligned.fits",
                "epoch2_flags_aligned.fits",
                "epoch2_alignment_footprint.fits",
            ):
                (project_dir / name).replace(processed_dir / name)

            with (
                patch.object(
                    improve_candidate_detection,
                    "get_data_path",
                    side_effect=lambda name, processed=False: (
                        (processed_dir if processed else raw_dir) / name
                    ),
                ),
                patch.object(improve_candidate_detection, "OUTPUT_FILE", output_file),
            ):
                improve_candidate_detection.detect_candidates()

            result = pd.read_csv(output_file)

        self.assertEqual(
            list(result.columns),
            ["x", "y", "difference", "significance", "type"],
        )
        self.assertEqual(set(result["type"]), {"positive", "negative"})
        self.assertFalse(((result["x"] == 0) & (result["y"] == 0)).any())
        self.assertTrue(result["significance"].abs().is_monotonic_decreasing)


if __name__ == "__main__":
    unittest.main()
