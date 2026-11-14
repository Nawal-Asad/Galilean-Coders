import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path


from pathlib import Path
import numpy as np
from astropy.io import fits


def read_hdu(filename, preferred=None):
    with fits.open(resolve_data_path(filename)) as hdul:
        if preferred is not None and preferred in hdul:
            return np.array(hdul[preferred].data, copy=True), hdul[preferred].header.copy()

        for hdu in hdul:
            if hdu.data is not None and hdu.data.ndim == 2:
                return np.array(hdu.data, copy=True), hdu.header.copy()

    raise ValueError(f"No 2D image found in {filename}")

epoch1, header1 = read_hdu("epoch1.fits", "IMAGE")
flags2, header2 = read_hdu("epoch2_flags_aligned.fits")
diff, _ = read_hdu("epoch2_minus_epoch1_difference.fits")

print("=== STEP 8: FLAG METADATA ===")

for name, header in [("Epoch 1", header1), ("Aligned Epoch 2 flags", header2)]:
    print(f"\n{name} header flag-related keywords:")
    for key in header:
        if any(word in key.upper() for word in ("FLAG", "MASK", "BIT", "QUAL", "DQ")):
            print(f"{key}: {header[key]}")

coordinates = [
    (1618, 247), (557, 598), (1340, 168),
    (35, 1401), (774, 780), (654, 1770)
]

print("\n=== PIXEL FLAG COMPARISON ===")

for x, y in coordinates:
    print(
        f"(x={x}, y={y}) | "
        f"Epoch 1={epoch1[y, x]} | "
        f"Epoch 2 flags={int(flags2[y, x])} | "
        f"Difference={diff[y, x]}"
    )

print("\nNo files were modified.")
