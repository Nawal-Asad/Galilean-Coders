
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astropy.io import fits
from reproject import reproject_interp
import numpy as np

from spherex.config import get_data_path, PROJECT_DIR

epoch1_file = get_data_path("epoch1.fits")
epoch2_file = get_data_path("epoch2.fits")

output_file = get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)

print("Opening Epoch 1 and Epoch 2...")

with fits.open(epoch1_file) as hdul1, fits.open(epoch2_file) as hdul2:
    reference_hdu = hdul1["IMAGE"]
    source_hdu = hdul2["IMAGE"]

    reference_data = reference_hdu.data
    source_data = source_hdu.data

    reference_wcs = reference_hdu.header
    source_wcs = source_hdu.header

    print("Epoch 1 shape:", reference_data.shape)
    print("Epoch 2 shape:", source_data.shape)
    print("Reprojecting Epoch 2 onto the Epoch 1 WCS grid...")

    aligned_data, footprint = reproject_interp(
        (source_data, source_wcs),
        reference_wcs,
        shape_out=reference_data.shape
    )

    output_header = reference_wcs.copy()
    output_header["COMMENT"] = (
        "Epoch 2 reprojected onto Epoch 1 IMAGE WCS grid"
    )

    fits.PrimaryHDU(
        data=aligned_data.astype(np.float32),
        header=output_header
    ).writeto(output_file, overwrite=True)

    footprint_file = get_data_path("epoch2_alignment_footprint.fits", processed=True)
    fits.PrimaryHDU(
        data=footprint.astype(np.float32),
        header=output_header
    ).writeto(footprint_file, overwrite=True)

    valid_pixels = np.count_nonzero(footprint > 0)
    total_pixels = footprint.size

    print("\nAlignment completed!")
    print("Aligned image:", output_file)
    print("Footprint image:", footprint_file)
    print("Pixels with coverage:", valid_pixels, "/", total_pixels)
    print("Coverage percentage:", round(100 * valid_pixels / total_pixels, 2), "%")
