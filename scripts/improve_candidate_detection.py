import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from astropy.io import fits
from scipy.ndimage import maximum_filter, minimum_filter

from spherex.config import get_data_path, get_result_path, PROJECT_DIR

OUTPUT_FILE = get_result_path("candidate_sources.csv")
BAD_FLAG_BITS = 2 | 64  # OVERFLOW and NONFUNC quality flags.


def detect_candidates():
    with fits.open(get_data_path("epoch1.fits")) as hdul:
        image1 = hdul["IMAGE"].data.astype(np.float32)
        variance1 = hdul["VARIANCE"].data.astype(np.float32)
        flags1 = hdul["FLAGS"].data.astype(np.int64)

    with fits.open(get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)) as hdul:
        image2 = hdul[0].data.astype(np.float32)

    with fits.open(get_data_path("epoch2_variance_aligned.fits", processed=True)) as hdul:
        variance2 = hdul[0].data.astype(np.float32)

    with fits.open(get_data_path("epoch2_flags_aligned.fits", processed=True)) as hdul:
        flags2 = hdul[0].data.astype(np.int64)

    with fits.open(get_data_path("epoch2_alignment_footprint.fits", processed=True)) as hdul:
        footprint = hdul[0].data

    maps = (image2, variance1, variance2, flags1, flags2, footprint)
    if any(image.shape != image1.shape for image in maps):
        raise ValueError("All input and aligned quality maps must have matching shapes.")

    valid = (
        np.isfinite(image1)
        & np.isfinite(image2)
        & np.isfinite(variance1)
        & (variance1 > 0)
        & np.isfinite(variance2)
        & (variance2 > 0)
        & (flags2 >= 0)
        & np.isfinite(footprint)
        & (footprint > 0)
        & ((flags1 & BAD_FLAG_BITS) == 0)
        & ((flags2 & BAD_FLAG_BITS) == 0)
    )

    difference = image2 - image1
    difference_variance = variance1 + variance2
    usable = valid & np.isfinite(difference_variance) & (difference_variance > 0)

    significance = np.full(image1.shape, np.nan, dtype=np.float32)
    significance[usable] = difference[usable] / np.sqrt(difference_variance[usable])

    safe_positive = np.where(usable, significance, -np.inf)
    safe_negative = np.where(usable, significance, np.inf)
    local_max = safe_positive == maximum_filter(safe_positive, size=5)
    local_min = safe_negative == minimum_filter(safe_negative, size=5)
    positive = np.argwhere(usable & local_max & (significance >= 5))
    negative = np.argwhere(usable & local_min & (significance <= -5))

    rows = [
        (int(x), int(y), float(difference[y, x]), float(significance[y, x]), "positive")
        for y, x in positive
    ]
    rows.extend(
        (int(x), int(y), float(difference[y, x]), float(significance[y, x]), "negative")
        for y, x in negative
    )
    rows.sort(key=lambda row: abs(row[3]), reverse=True)

    output = np.array(
        rows,
        dtype=[
            ("x", "i4"),
            ("y", "i4"),
            ("difference", "f8"),
            ("significance", "f8"),
            ("type", "U8"),
        ],
    )
    temporary_file = OUTPUT_FILE.with_suffix(".csv.tmp")
    np.savetxt(
        temporary_file,
        output,
        delimiter=",",
        header="x,y,difference,significance,type",
        fmt=["%d", "%d", "%.6f", "%.3f", "%s"],
        comments="",
    )
    temporary_file.replace(OUTPUT_FILE)
    print("Valid comparison pixels:", int(usable.sum()))
    print("Positive candidates (>5 sigma):", len(positive))
    print("Negative candidates (<-5 sigma):", len(negative))
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    detect_candidates()
