import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from pathlib import Path
import numpy as np
from astropy.io import fits

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

files = {
    "Epoch 1": get_data_path("epoch1.fits"),
    "Epoch 2 aligned": get_data_path("epoch2_aligned_to_epoch1.fits", processed=True),
    "Difference": get_data_path("epoch2_minus_epoch1_difference.fits", processed=True),
    "Footprint": get_data_path("epoch2_alignment_footprint.fits", processed=True),
}

arrays = {}

for name, path in files.items():
    print(f"\n--- {name} ---")
    print("File exists:", path.exists())

    if not path.exists():
        continue

    with fits.open(path) as hdul:
        hdu = hdul["IMAGE"] if name == "Epoch 1" else hdul[0]
        data = hdu.data.astype(np.float64)

    arrays[name] = data
    finite = data[np.isfinite(data)]

    print("Shape:", data.shape)
    print("Finite pixels:", finite.size)

    if finite.size:
        print("Min:", np.min(finite))
        print("1st percentile:", np.percentile(finite, 1))
        print("Median:", np.median(finite))
        print("99th percentile:", np.percentile(finite, 99))
        print("Max:", np.max(finite))

if all(name in arrays for name in files):
    epoch1 = arrays["Epoch 1"]
    epoch2 = arrays["Epoch 2 aligned"]
    difference = arrays["Difference"]
    footprint = arrays["Footprint"]

    valid = (
        np.isfinite(epoch1)
        & np.isfinite(epoch2)
        & np.isfinite(difference)
        & np.isfinite(footprint)
        & (footprint > 0)
    )

    indices = np.argwhere(valid)
    order = np.argsort(np.abs(difference[valid]))[::-1][:10]
    top_indices = indices[order]

    print("\n--- Ten largest absolute differences ---")

    for y, x in top_indices:
        print(
            f"x={x}, y={y}, "
            f"Epoch1={epoch1[y, x]:.6f}, "
            f"Epoch2={epoch2[y, x]:.6f}, "
            f"Difference={difference[y, x]:.6f}"
        )

    print("\nDiagnostic check completed.")
