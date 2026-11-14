
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
from astropy.visualization import ImageNormalize, PercentileInterval, AsinhStretch

from spherex.config import get_data_path, get_result_path

with fits.open(get_data_path("epoch1.fits")) as hdul:
    image_data = hdul["IMAGE"].data

# Ignore invalid pixels when calculating display limits
valid_pixels = image_data[np.isfinite(image_data)]

# Stretch the image to reveal faint features
norm = ImageNormalize(
    image_data,
    interval=PercentileInterval(99.5),
    stretch=AsinhStretch()
)

plt.figure(figsize=(10, 8))
plt.imshow(
    image_data,
    origin="lower",
    cmap="inferno",
    norm=norm,
    interpolation="nearest"
)

plt.colorbar(label="Image pixel value")
plt.title("SPHEREx Epoch 1 — Band D2 (Enhanced Contrast)")
plt.xlabel("Pixel X")
plt.ylabel("Pixel Y")
plt.tight_layout()

plt.savefig(get_result_path("epoch1_visualization_enhanced.png"), dpi=150)
plt.show()

print("Finite pixels:", valid_pixels.size)
print("Enhanced image saved successfully.")
