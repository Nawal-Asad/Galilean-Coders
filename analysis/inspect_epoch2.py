import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pathlib import Path
from astropy.io import fits

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

# Epoch 2 FITS file ka path
fits_file = get_data_path("epoch2.fits")

print("Checking Epoch 2 file...")
print("File path:", fits_file.resolve())
print("File exists:", fits_file.exists())

if fits_file.exists():
    print("\nInspecting FITS structure...\n")

    with fits.open(fits_file) as hdul:
        hdul.info()

        print("\n--- Image Information ---")

        if "IMAGE" in hdul:
            image = hdul["IMAGE"].data

            print("Image shape:", image.shape)
            print("Number of dimensions:", image.ndim)
            print("Data type:", image.dtype)
        else:
            print("IMAGE extension not found.")

    print("\nEpoch 2 inspection completed!")

else:
    print("\nERROR: epoch2.fits file not found.")
    print("Make sure it is in the same folder as this Python script.")
