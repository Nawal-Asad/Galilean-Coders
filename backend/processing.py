
import numpy as np
from astropy.io import fits

from spherex.config import get_data_path


def load_image(filename):
    """Load the IMAGE extension from a SPHEREx FITS file."""
    file_path = get_data_path(filename, processed=False)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with fits.open(file_path) as hdul:
        image = hdul["IMAGE"].data.astype(np.float32).copy()

    return image


def compare_epochs():
    """Compare Epoch 1 with the already aligned Epoch 2 image."""
    epoch1 = load_image("epoch1.fits")
    with fits.open(get_data_path("epoch1.fits")) as hdul:
        brightness_unit = hdul["IMAGE"].header.get("BUNIT", "unknown")

    aligned_path = get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)

    if not aligned_path.exists():
        raise FileNotFoundError(
            f"Aligned image not found: {aligned_path}"
        )

    with fits.open(aligned_path) as hdul:
        epoch2 = hdul[0].data.astype(np.float32).copy()

    if epoch1.shape != epoch2.shape:
        raise ValueError("Epoch images have different shapes.")

    difference = epoch2 - epoch1

    valid = np.isfinite(difference)
    valid_count = int(valid.sum())

    if valid_count == 0:
        raise ValueError("No finite pixels are available for comparison.")

    return {
        "epoch1_shape": list(epoch1.shape),
        "epoch2_shape": list(epoch2.shape),
        "valid_pixels": valid_count,
        "mean_difference": float(np.mean(difference[valid])),
        "median_difference": float(np.median(difference[valid])),
        "difference_unit": str(brightness_unit),
    }
