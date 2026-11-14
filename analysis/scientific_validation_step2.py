import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path


from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io import fits

CSV_FILE = get_result_path("candidate_sources.csv")


def read_fits_data(filename):
    path = resolve_data_path(filename)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with fits.open(path) as hdul:
        for hdu in hdul:
            data = hdu.data

            if data is not None and data.ndim == 2:
                return np.array(data, copy=True)

    raise ValueError(f"No 2D image found in {filename}")


# Load candidate records and FITS maps
df = pd.read_csv(CSV_FILE)

epoch1 = read_fits_data("epoch1.fits")
epoch2 = read_fits_data("epoch2_aligned_to_epoch1.fits")
difference = read_fits_data("epoch2_minus_epoch1_difference.fits")
footprint = read_fits_data("epoch2_alignment_footprint.fits")

print("\n=== STEP 2: FITS QUALITY INVESTIGATION ===")

for name, image in [
    ("Epoch 1", epoch1),
    ("Aligned Epoch 2", epoch2),
    ("Difference", difference),
    ("Footprint", footprint),
]:
    print(f"\n{name}:")
    print("Shape:", image.shape)
    print("Finite pixels:", int(np.isfinite(image).sum()))
    print("Non-finite pixels:", int((~np.isfinite(image)).sum()))

# Check whether all maps have the expected shape
expected_shape = epoch1.shape

for name, image in [
    ("Epoch 2", epoch2),
    ("Difference", difference),
    ("Footprint", footprint),
]:
    if image.shape != expected_shape:
        raise ValueError(
            f"{name} shape {image.shape} does not match {expected_shape}"
        )

# Candidate coordinates: x is column, y is row
x = df["x"].to_numpy(dtype=int)
y = df["y"].to_numpy(dtype=int)

candidate_difference = difference[y, x]
candidate_epoch1 = epoch1[y, x]
candidate_epoch2 = epoch2[y, x]
candidate_footprint = footprint[y, x]

csv_difference = df["difference"].to_numpy(dtype=float)
csv_significance = df["significance"].to_numpy(dtype=float)

print("\n=== CANDIDATE PIXEL CHECKS ===")

print(
    "Candidates with non-finite difference image pixels:",
    int((~np.isfinite(candidate_difference)).sum())
)

print(
    "Candidates with non-finite Epoch 1 pixels:",
    int((~np.isfinite(candidate_epoch1)).sum())
)

print(
    "Candidates with non-finite aligned Epoch 2 pixels:",
    int((~np.isfinite(candidate_epoch2)).sum())
)

print(
    "Candidates with zero footprint:",
    int((candidate_footprint <= 0).sum())
)

print(
    "Candidates with non-finite footprint:",
    int((~np.isfinite(candidate_footprint)).sum())
)

# Compare saved CSV values with the actual difference FITS
both_finite = (
    np.isfinite(csv_difference)
    & np.isfinite(candidate_difference)
)

if both_finite.any():
    delta = np.abs(
        csv_difference[both_finite]
        - candidate_difference[both_finite]
    )

    print("\nCSV versus difference FITS:")
    print("Comparable records:", int(both_finite.sum()))
    print("Median absolute mismatch:", float(np.median(delta)))
    print("Maximum absolute mismatch:", float(np.max(delta)))
    print("Mismatches > 0.001:", int((delta > 0.001).sum()))

print("\n=== MISSING VALUE PATTERN ===")

missing_measurements = (
    ~np.isfinite(csv_difference)
    | ~np.isfinite(csv_significance)
)

print("Records with missing measurements:", int(missing_measurements.sum()))

print(
    "Missing-measurement records with zero footprint:",
    int(((candidate_footprint <= 0) & missing_measurements).sum())
)

print(
    "Missing-measurement records with non-finite difference pixels:",
    int(((~np.isfinite(candidate_difference)) & missing_measurements).sum())
)

print("\nInvestigation complete. No files were modified.")
