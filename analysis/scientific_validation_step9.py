import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path


from pathlib import Path
from astropy.io import fits


for filename in ["epoch1.fits", "epoch2.fits", "epoch2_flags_aligned.fits"]:
    path = resolve_data_path(filename)

    print(f"\n=== {filename} ===")

    if not path.exists():
        print("File not found")
        continue

    with fits.open(path) as hdul:
        for i, hdu in enumerate(hdul):
            print(f"\nHDU {i}: {hdu.name}")
            print("Shape:", getattr(hdu.data, "shape", None))

            for key in hdu.header:
                if key.startswith("MP_") or "MP_" in key:
                    print(f"{key}: {hdu.header[key]}")

            for key in hdu.header:
                if key in ["EXTNAME", "L1DQAFLG", "L2DQAFLG", "SPS_FLAGS"]:
                    print(f"{key}: {hdu.header[key]}")

print("\nInspection complete. No files were modified.")
