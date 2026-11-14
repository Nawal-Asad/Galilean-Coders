import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import requests
import time
from pathlib import Path
from astropy.io import fits

from spherex.config import get_data_path

url = (
    "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2/level2/"
    "2025W25_2A/l2b-v20-2025-254/2/"
    "level2_2025W25_2A_0196_1D2_spx_l2b-v20-2025-254.fits"
)

output_file = get_data_path("epoch1.fits")
expected_size = 71634240
downloaded = False

for attempt in range(1, 6):
    try:
        print(f"\nDownload attempt {attempt}/5")

        with requests.get(
            url,
            stream=True,
            timeout=(20, 60),
        ) as response:
            response.raise_for_status()

            if response.headers.get("Content-Type", "").startswith("text/"):
                raise ValueError("The server returned text instead of FITS data.")

            temp_file = get_data_path("epoch1_download.tmp")
            total = 0

            with temp_file.open("wb") as file:
                for chunk in response.iter_content(chunk_size=256 * 1024):
                    if chunk:
                        file.write(chunk)
                        total += len(chunk)
                        print(
                            f"\rDownloaded {total / (1024 * 1024):.1f} MiB",
                            end="",
                            flush=True,
                        )

        if total != expected_size:
            raise ValueError(
                f"Incomplete download: received {total} bytes."
            )

        temp_file.replace(output_file)
        downloaded = True
        print("\nDownload complete!")
        break

    except (requests.RequestException, OSError, ValueError) as error:
        print(f"\nAttempt failed: {error}")
        if attempt < 5:
            print("Waiting 5 seconds before retrying...")
            time.sleep(5)

if downloaded:
    print("\nChecking FITS file...")
    with fits.open(output_file) as hdul:
        hdul.info()

    print("\nSuccess! The FITS file opened correctly.")
else:
    print("\nDownload unsuccessful after 5 attempts.")
    print("No complete FITS file was saved as epoch1.fits.")
