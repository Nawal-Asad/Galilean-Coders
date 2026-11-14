import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import ImageNormalize, AsinhStretch

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

# Load Epoch 1
with fits.open(get_data_path("epoch1.fits")) as hdul:
    epoch1 = hdul["IMAGE"].data.astype(float)

# Load aligned Epoch 2
with fits.open(get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)) as hdul:
    epoch2 = hdul[0].data.astype(float)

# Load difference image
with fits.open(get_data_path("epoch2_minus_epoch1_difference.fits", processed=True)) as hdul:
    difference = hdul[0].data.astype(float)

# Prominent blue spot from your image
x, y = 1178, 1210

# Zoom area around the selected spot
radius = 40
x1, x2 = max(0, x-radius), min(epoch1.shape[1], x+radius)
y1, y2 = max(0, y-radius), min(epoch1.shape[0], y+radius)

images = [
    (epoch1, "Epoch 1"),
    (epoch2, "Aligned Epoch 2"),
    (difference, "Epoch 2 - Epoch 1")
]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for ax, (image, title) in zip(axes, images):
    cutout = image[y1:y2, x1:x2]
    finite = cutout[np.isfinite(cutout)]

    if finite.size:
        vmin, vmax = np.percentile(finite, [5, 99])
        norm = ImageNormalize(
            vmin=vmin,
            vmax=vmax,
            stretch=AsinhStretch()
        )
        ax.imshow(
            cutout,
            origin="lower",
            cmap="gray" if title != "Epoch 2 - Epoch 1" else "coolwarm",
            norm=norm
        )

    ax.set_title(title)
    ax.set_xlabel("X pixel")
    ax.set_ylabel("Y pixel")

plt.suptitle(f"Zoomed Region around x={x}, y={y}")
plt.tight_layout()
plt.savefig(get_result_path("candidate_region_comparison.png"), dpi=150)
plt.show()

print("Saved: candidate_region_comparison.png")
