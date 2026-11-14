import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import numpy as np
from astropy.io import fits
from reproject import reproject_interp

from spherex.config import get_data_path

# Original FITS files
epoch1_file = get_data_path("epoch1.fits")
epoch2_file = get_data_path("epoch2.fits")

# Open both observations
with fits.open(epoch1_file) as hdul1, fits.open(epoch2_file) as hdul2:

    # Epoch 1 is our reference grid
    reference_header = hdul1["IMAGE"].header.copy()
    reference_shape = hdul1["IMAGE"].data.shape

    # Read Epoch 2 quality maps
    flags_data = hdul2["FLAGS"].data
    variance_data = hdul2["VARIANCE"].data
    epoch2_header = hdul2["IMAGE"].header.copy()

    # Align FLAGS using nearest-neighbor interpolation
    aligned_flags, flags_footprint = reproject_interp(
        (flags_data, epoch2_header),
        reference_header,
        shape_out=reference_shape,
        order="nearest-neighbor"
    )

    # Align VARIANCE using interpolation
    aligned_variance, variance_footprint = reproject_interp(
        (variance_data, epoch2_header),
        reference_header,
        shape_out=reference_shape,
        order="bilinear"
    )

# Save aligned FLAGS as integers; -1 marks outside coverage
aligned_flags = np.where(
    flags_footprint > 0,
    np.nan_to_num(aligned_flags, nan=-1),
    -1
).astype(np.int32)

# Save aligned VARIANCE
aligned_variance = np.where(
    variance_footprint > 0,
    aligned_variance,
    np.nan
).astype(np.float32)

fits.PrimaryHDU(aligned_flags).writeto(
    get_data_path("epoch2_flags_aligned.fits", processed=True), overwrite=True
)

fits.PrimaryHDU(aligned_variance).writeto(
    get_data_path("epoch2_variance_aligned.fits", processed=True), overwrite=True
)

print("Quality maps aligned successfully!")
print("FLAGS shape:", aligned_flags.shape)
print("VARIANCE shape:", aligned_variance.shape)
print("Valid FLAGS pixels:", np.sum(aligned_flags >= 0))
print("Valid VARIANCE pixels:", np.sum(np.isfinite(aligned_variance)))
