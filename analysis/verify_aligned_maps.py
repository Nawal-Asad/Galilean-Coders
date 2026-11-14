
import numpy as np
from astropy.io import fits

# Epoch 1 image is stored in the IMAGE extension
files = [
    ("epoch1.fits", "IMAGE"),
    ("epoch2_flags_aligned.fits", 0),
    ("epoch2_variance_aligned.fits", 0),
]

for filename, extension in files:
    print(f"\n--- {filename} ---")

    with fits.open(filename) as hdul:
        data = hdul[extension].data

        if data is None:
            print("ERROR: No data found in this extension.")
            continue

        print("Shape:", data.shape)
        print("Data type:", data.dtype)
        print("Finite pixels:", np.isfinite(data).sum())

        if "variance" in filename.lower():
            valid = data[np.isfinite(data) & (data > 0)]

            if valid.size:
                print("Median positive variance:", np.median(valid))

        elif "flags" in filename.lower():
            valid = data[data >= 0]

            if valid.size:
                print("Valid flag pixels:", valid.size)
                print("Unique flag values (first 15):",
                      np.unique(valid)[:15])
