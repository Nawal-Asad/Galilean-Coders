import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path

from pathlib import Path
import numpy as np
from astropy.io import fits


def read_image(filename):
    with fits.open(resolve_data_path(filename)) as hdul:
        for hdu in hdul:
            if hdu.data is not None and hdu.data.ndim == 2:
                return np.array(hdu.data, dtype=np.float64, copy=True)
    raise ValueError(f"No 2D image found: {filename}")

epoch1 = read_image("epoch1.fits")
epoch2 = read_image("epoch2_aligned_to_epoch1.fits")
difference = read_image("epoch2_minus_epoch1_difference.fits")
footprint = read_image("epoch2_alignment_footprint.fits")

valid = (
    np.isfinite(epoch1)
    & np.isfinite(epoch2)
    & np.isfinite(difference)
    & np.isfinite(footprint)
    & (footprint > 0)
)

indices = np.flatnonzero(valid)
top = indices[
    np.argsort(np.abs(difference.ravel()[indices]))[-10:][::-1]
]

print("=== STEP 6: COMPARE EXTREME PIXELS ===")
print("x | y | Epoch 1 | Epoch 2 | Difference")

for idx in top:
    y, x = np.unravel_index(idx, difference.shape)
    print(
        f"{x} | {y} | "
        f"{epoch1[y, x]:.6f} | "
        f"{epoch2[y, x]:.6f} | "
        f"{difference[y, x]:.6f}"
    )

print("\nNo files were modified.")