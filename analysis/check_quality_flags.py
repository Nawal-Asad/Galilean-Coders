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
    "Epoch 2": get_data_path("epoch2.fits"),
}

for epoch, filepath in files.items():
    print(f"\n{'=' * 40}")
    print(epoch)
    print("=" * 40)

    with fits.open(filepath) as hdul:
        image = hdul["IMAGE"].data
        flags = hdul["FLAGS"].data
        variance = hdul["VARIANCE"].data

        print("Image shape:", image.shape)
        print("Flags shape:", flags.shape)
        print("Variance shape:", variance.shape)

        print("\nImage header flag-related keywords:")
        header = hdul["FLAGS"].header

        for key in header:
            if any(word in key.upper() for word in ["FLAG", "MASK", "BIT"]):
                print(f"{key}: {header[key]}")

        print("\nFlag values:")
        values, counts = np.unique(flags, return_counts=True)

        for value, count in zip(values[:20], counts[:20]):
            print(f"Flag {value}: {count} pixels")

        if len(values) > 20:
            print("Showing first 20 unique flag values only.")

        finite_var = variance[np.isfinite(variance)]
        print("\nVariance statistics:")
        print("Minimum:", np.min(finite_var))
        print("Median:", np.median(finite_var))
        print("Maximum:", np.max(finite_var))

        test_pixels = (
            [(247, 1618), (168, 1340)]
            if epoch == "Epoch 1"
            else [(247, 1618), (168, 1340)]
        )

        print("\nSelected pixel quality:")
        for y, x in test_pixels:
            print(
                f"(x={x}, y={y}): "
                f"image={image[y, x]}, "
                f"flags={flags[y, x]}, "
                f"variance={variance[y, x]}"
            )

print("\nQuality inspection completed!")
