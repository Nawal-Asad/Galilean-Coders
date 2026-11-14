import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import numpy as np
from astropy.io import fits

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

# Load images and quality maps
with fits.open(get_data_path("epoch1.fits")) as hdul:
    image1 = hdul["IMAGE"].data.astype(float)
    flags1 = hdul["FLAGS"].data

with fits.open(get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)) as hdul:
    image2 = hdul[0].data.astype(float)

with fits.open(get_data_path("epoch2_flags_aligned.fits", processed=True)) as hdul:
    flags2 = hdul[0].data

with fits.open(get_data_path("epoch1.fits")) as hdul:
    variance1 = hdul["VARIANCE"].data.astype(float)

with fits.open(get_data_path("epoch2_variance_aligned.fits", processed=True)) as hdul:
    variance2 = hdul[0].data.astype(float)

# Exclude OVERFLOW (bit 2) and NONFUNC (bit 64)
bad_bits = 2 | 64

valid = (
    np.isfinite(image1)
    & np.isfinite(image2)
    & np.isfinite(variance1)
    & np.isfinite(variance2)
    & (variance1 > 0)
    & (variance2 > 0)
    & (flags2 >= 0)
    & ((flags1 & bad_bits) == 0)
    & ((flags2 & bad_bits) == 0)
)

difference = image2 - image1
total_variance = variance1 + variance2

significance = np.full(image1.shape, np.nan)
significance[valid] = (
    difference[valid] / np.sqrt(total_variance[valid])
)

print("Total image pixels:", image1.size)
print("Valid pixels after quality filtering:", valid.sum())
print("Rejected pixels:", image1.size - valid.sum())

values = significance[valid]

print("\nSignificance percentiles:")
for p in [1, 5, 25, 50, 75, 95, 99]:
    print(f"{p}%:", np.percentile(values, p))

print("\nPixels beyond thresholds:")
for threshold in [3, 5, 10]:
    print(
        f"|significance| > {threshold}:",
        np.sum(np.abs(values) > threshold)
    )

print("\nValidation completed.")
