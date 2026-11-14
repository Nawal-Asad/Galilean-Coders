import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from pathlib import Path
from astropy.io import fits

from spherex.config import get_data_path, get_result_path

files = ["epoch1.fits", "epoch2.fits"]

keys = [
    "CRPIX1", "CRPIX2",
    "CRVAL1", "CRVAL2",
    "CDELT1", "CDELT2",
    "CD1_1", "CD1_2",
    "CD2_1", "CD2_2",
    "CTYPE1", "CTYPE2"
]

for filename in files:
    filepath = get_data_path(filename)

    print("\n" + "=" * 40)
    print("FILE:", filename)
    print("=" * 40)

    with fits.open(filepath) as hdul:
        header = hdul["IMAGE"].header

        for key in keys:
            print(f"{key}: {header.get(key, 'Not present')}")

print("\nWCS keyword check completed!")
