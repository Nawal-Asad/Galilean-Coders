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
saved_difference = read_image("epoch2_minus_epoch1_difference.fits")

recomputed_difference = epoch2 - epoch1

valid = (
    np.isfinite(epoch1)
    & np.isfinite(epoch2)
    & np.isfinite(saved_difference)
)

delta = saved_difference[valid] - recomputed_difference[valid]

print("=== STEP 4: DIFFERENCE VERIFICATION ===")
print("Comparable pixels:", int(valid.sum()))
print("Median saved difference:", float(np.median(saved_difference[valid])))
print("Median recomputed difference:", float(np.median(recomputed_difference[valid])))
print("Median absolute mismatch:", float(np.median(np.abs(delta))))
print("Maximum absolute mismatch:", float(np.max(np.abs(delta))))
print("Pixels with mismatch > 0.001:", int((np.abs(delta) > 0.001).sum()))

print("\n=== EXTREME PIXELS ===")
abs_diff = np.abs(saved_difference)
finite = np.isfinite(abs_diff)
print("Maximum absolute difference:", float(np.max(abs_diff[finite])))
print("Pixels with |difference| > 1:", int((abs_diff[finite] > 1).sum()))
print("Pixels with |difference| > 10:", int((abs_diff[finite] > 10).sum()))
print("Pixels with |difference| > 100:", int((abs_diff[finite] > 100).sum()))

print("\nNo files were modified.")