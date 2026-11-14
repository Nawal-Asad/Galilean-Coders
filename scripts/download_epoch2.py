import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import urllib.request

from spherex.config import get_data_path
# Epoch 2 FITS file ka direct URL

url = (
    "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2/"
    "level2/2025W51_1A/l2b-v21-2025-354/2/"
    "level2_2025W51_1A_0635_2D2_spx_l2b-v21-2025-354.fits"
)

# Downloaded file ka naam
output_file = get_data_path("epoch2.fits")
temp_file = get_data_path("epoch2.fits.part")

try:
    print("Downloading Epoch 2 FITS file...")
    print("Please wait; the file may be large.")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type", "")
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0

        with open(temp_file, "wb") as file:
            while True:
                chunk = response.read(1024 * 1024)

                if not chunk:
                    break

                file.write(chunk)
                downloaded += len(chunk)

                if total_size:
                    percent = downloaded * 100 / total_size
                    print(
                        f"\rProgress: {percent:.1f}%",
                        end=""
                    )

    if total_size and downloaded != total_size:
        raise IOError("Download incomplete. Please run again.")

    # Check that the server returned a FITS file, not an error page
    with open(temp_file, "rb") as file:
        signature = file.read(30)

    if not signature.startswith(b"SIMPLE"):
        raise ValueError(
            "Downloaded response is not a valid FITS file. "
            "Check the URL or server response."
        )

    temp_file.replace(output_file)

    print("\n\nDownload successful!")
    print("Saved at:", output_file)
    print(f"File size: {downloaded / (1024**2):.2f} MB")

except Exception as error:
    print("\nDownload failed:", error)
    print("Check your internet connection and try again.")
    print("If a partial file exists, it is kept as .part.")
