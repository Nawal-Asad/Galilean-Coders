
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spherex.config import RAW_DIR, get_data_path

files = {
    "Epoch 1": get_data_path("epoch1.fits"),
    "Epoch 2": get_data_path("epoch2.fits"),
}

for epoch, filepath in files.items():
    print(f"\n{'=' * 45}")
    print(epoch)
    print("=" * 45)

    if not filepath.exists():
        print("File not found:", filepath)
        continue

    print("File:", filepath.name)
    print("File size:", round(filepath.stat().st_size / (1024**2), 2), "MB")

    with fits.open(filepath) as hdul:
        print("FITS opened successfully!")

        print("\nAvailable HDUs:")
        hdul.info()

        if "IMAGE" not in hdul:
            print("IMAGE extension not found.")
            continue

        image = hdul["IMAGE"].data
        header = hdul["IMAGE"].header

        print("\nImage shape:", image.shape)
        print("Data type:", image.dtype)
        print("Observation date:", header.get("DATE-OBS", "Not available"))
        print("MJD:", header.get("MJD-OBS", "Not available"))
        print("RA (degrees):", header.get("CRVAL1", "Not available"))
        print("Dec (degrees):", header.get("CRVAL2", "Not available"))
        print("Brightness unit:", header.get("BUNIT", "Not available"))
        print("Coordinate type:", header.get("CTYPE1", "Not available"))

print("\nEpoch information check completed!")

