import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import ImageNormalize, AsinhStretch

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

with fits.open(get_data_path("epoch2_minus_epoch1_difference.fits", processed=True)) as hdul:
    difference = hdul[0].data.astype(float)

finite = np.isfinite(difference)
values = difference[finite]

vmin, vmax = np.percentile(values, [1, 99])

norm = ImageNormalize(
    vmin=vmin,
    vmax=vmax,
    stretch=AsinhStretch()
)

plt.figure(figsize=(10, 8))
plt.imshow(
    difference,
    origin="lower",
    cmap="coolwarm",
    norm=norm
)
plt.colorbar(label="Epoch 2 - Epoch 1 (MJy/sr)")
plt.title("Difference Image: Epoch 2 minus Epoch 1")
plt.xlabel("X pixel")
plt.ylabel("Y pixel")
plt.tight_layout()
plt.savefig(get_result_path("difference_regions_inspection.png"), dpi=150)
plt.show()

print("Saved: difference_regions_inspection.png")
print("Display range:", vmin, "to", vmax)
