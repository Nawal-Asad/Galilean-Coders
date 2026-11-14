import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from astropy.io import fits

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

fits_file = get_data_path("epoch2.fits")

with fits.open(fits_file) as hdul:
    header = hdul["IMAGE"].header
    image = hdul["IMAGE"].data

    print("=" * 45)
    print("SPHEREx EPOCH 2 — OBSERVATION INFO")
    print("=" * 45)

    print("Epoch: 2")
    print("Observation file:", fits_file.name)
    print("Date observed:", header.get("DATE-OBS", "Not available"))
    print("MJD observed:", header.get("MJD-OBS", "Not available"))
    print("RA (degrees):", header.get("CRVAL1", "Not available"))
    print("Dec (degrees):", header.get("CRVAL2", "Not available"))
    print("Image width (pixels):", image.shape[1])
    print("Image height (pixels):", image.shape[0])
    print("Brightness unit:", header.get("BUNIT", "Not available"))
    print("Image HDU: IMAGE")
    print("Band: D2")

    print("\nEpoch 2 observation info completed!")
