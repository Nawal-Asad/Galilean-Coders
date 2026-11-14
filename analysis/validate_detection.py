import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import numpy as np
from astropy.io import fits

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

with fits.open(get_data_path("epoch1.fits")) as h:
    image1 = h["IMAGE"].data.astype(float)
    variance1 = h["VARIANCE"].data.astype(float)
    flags1 = h["FLAGS"].data.astype(np.int64)

with fits.open(get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)) as h:
    image2 = h[0].data.astype(float)

with fits.open(get_data_path("epoch2_variance_aligned.fits", processed=True)) as h:
    variance2 = h[0].data.astype(float)

with fits.open(get_data_path("epoch2_flags_aligned.fits", processed=True)) as h:
    flags2 = h[0].data.astype(np.int64)

difference = image2 - image1
total_variance = variance1 + variance2

valid = (
    np.isfinite(difference)
    & np.isfinite(total_variance)
    & (total_variance > 0)
    & (flags2 >= 0)
    & ((flags1 & (2 | 64)) == 0)
    & ((flags2 & (2 | 64)) == 0)
)

snr = difference[valid] / np.sqrt(total_variance[valid])

print("Significance percentiles:")
for p in [0, 1, 5, 25, 50, 75, 95, 99, 100]:
    print(f"{p}%: {np.percentile(snr, p):.3f}")

print("\nThreshold counts:")
for threshold in [3, 5, 10, 20]:
    print(
        f">{threshold} sigma:",
        np.sum(snr > threshold),
        "|",
        f"<-{threshold} sigma:",
        np.sum(snr < -threshold)
    )

print("\nDifference percentiles:")
print(np.percentile(difference[valid], [1, 50, 99]))
