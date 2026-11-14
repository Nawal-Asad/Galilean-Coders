import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import ImageNormalize, AsinhStretch

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

with fits.open(get_data_path("epoch1.fits")) as hdul:
    image1 = hdul["IMAGE"].data.astype(float)
    flags1 = hdul["FLAGS"].data
    variance1 = hdul["VARIANCE"].data.astype(float)

with fits.open(get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)) as hdul:
    image2 = hdul[0].data.astype(float)

with fits.open(get_data_path("epoch2_flags_aligned.fits", processed=True)) as hdul:
    flags2 = hdul[0].data

with fits.open(get_data_path("epoch2_variance_aligned.fits", processed=True)) as hdul:
    variance2 = hdul[0].data.astype(float)

bad_bits = 2 | 64

valid = (
    np.isfinite(image1)
    & np.isfinite(image2)
    & np.isfinite(variance1)
    & np.isfinite(variance2)
    & (variance1 > 0)
    & (variance2 > 0)
    & (flags2 >= 0)
    & ((flags1 & bad_bits) == 0)
    & ((flags2 & bad_bits) == 0)
)

significance = np.full(image1.shape, np.nan)
significance[valid] = (
    (image2[valid] - image1[valid])
    / np.sqrt(variance1[valid] + variance2[valid])
)

display = np.clip(significance, -10, 10)

plt.figure(figsize=(10, 8))
plt.imshow(
    display,
    origin="lower",
    cmap="coolwarm",
    vmin=-10,
    vmax=10
)
plt.colorbar(label="Difference significance (clipped to ±10)")
plt.title("Exploratory Significance Map")
plt.xlabel("X pixel")
plt.ylabel("Y pixel")
plt.tight_layout()
plt.savefig(get_result_path("significance_map.png"), dpi=150)
plt.show()

print("Saved: significance_map.png")
print("This map is exploratory, not a validated detection map.")
