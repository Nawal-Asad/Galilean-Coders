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
                return np.array(hdu.data, copy=True)
    raise ValueError(f"No 2D image found: {filename}")

difference = read_image("epoch2_minus_epoch1_difference.fits")
flags = read_image("epoch2_flags_aligned.fits")
epoch1 = read_image("epoch1.fits")

coordinates = [
    (1618, 247),
    (1615, 247),
    (557, 598),
    (1614, 246),
    (1340, 168),
    (558, 599),
    (35, 1401),
    (559, 599),
    (774, 780),
    (654, 1770),
]

print("=== STEP 7: QUALITY FLAG CHECK ===")

for x, y in coordinates:
    y0, y1 = max(0, y - 2), min(difference.shape[0], y + 3)
    x0, x1 = max(0, x - 2), min(difference.shape[1], x + 3)

    local_diff = difference[y0:y1, x0:x1]
    local_flags = flags[y0:y1, x0:x1]

    print(f"\nPixel (x={x}, y={y})")
    print("Epoch 1:", float(epoch1[y, x]))
    print("Difference:", float(difference[y, x]))
    print("Flag value:", int(flags[y, x]))
    print("Local 5x5 finite difference pixels:",
          int(np.isfinite(local_diff).sum()))
    print("Local 5x5 flag values and counts:",
          {str(v): int(n) for v, n in zip(
              *np.unique(local_flags, return_counts=True)
          )})

print("\nNo files were modified.")
