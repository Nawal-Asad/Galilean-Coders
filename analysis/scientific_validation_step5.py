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

diff = read_image("epoch2_minus_epoch1_difference.fits")
footprint = read_image("epoch2_alignment_footprint.fits")

valid = np.isfinite(diff) & np.isfinite(footprint) & (footprint > 0)
yy, xx = np.indices(diff.shape)
edge_distance = np.minimum.reduce([
    xx, yy, diff.shape[1] - 1 - xx, diff.shape[0] - 1 - yy
])

print("=== STEP 5: EXTREME PIXEL LOCATIONS ===")

for threshold in [1, 10, 100]:
    mask = valid & (np.abs(diff) > threshold)
    print(f"\n|Difference| > {threshold}:")
    print("Pixel count:", int(mask.sum()))
    if mask.any():
        print("Within 10 pixels of edge:", int((mask & (edge_distance < 10)).sum()))
        print("Within 50 pixels of edge:", int((mask & (edge_distance < 50)).sum()))
        print("Median absolute difference:", float(np.median(np.abs(diff[mask]))))

mask = valid
indices = np.flatnonzero(mask)
top = indices[np.argsort(np.abs(diff.ravel()[indices]))[-10:][::-1]]

print("\nTop 10 extreme valid pixels (x, y, difference):")
for idx in top:
    y, x = np.unravel_index(idx, diff.shape)
    print(int(x), int(y), float(diff[y, x]))

print("\nNo files were modified.")