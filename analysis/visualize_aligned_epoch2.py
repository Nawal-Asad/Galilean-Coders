import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from pathlib import Path
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import (
    ImageNormalize,
    PercentileInterval,
    AsinhStretch,
)
import numpy as np

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

image_file = get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)
footprint_file = get_data_path("epoch2_alignment_footprint.fits", processed=True)

with fits.open(image_file) as hdul:
    image = hdul[0].data.copy()

with fits.open(footprint_file) as hdul:
    footprint = hdul[0].data.copy()

valid = np.isfinite(image) & (footprint > 0)

display_image = np.where(valid, image, np.nan)

norm = ImageNormalize(
    display_image,
    interval=PercentileInterval(99.5),
    stretch=AsinhStretch(),
)

plt.figure(figsize=(10, 8))
plt.imshow(
    display_image,
    origin="lower",
    cmap="inferno",
    norm=norm,
)
plt.colorbar(label="Brightness (MJy / sr)")
plt.title("Epoch 2 Aligned to Epoch 1 Grid")
plt.xlabel("X Pixel")
plt.ylabel("Y Pixel")
plt.tight_layout()

output_file = get_result_path("epoch2_aligned_visualization.png")
plt.savefig(output_file, dpi=150)
plt.show()

print("Aligned visualization saved:", output_file)
print("Valid covered pixels:", np.count_nonzero(valid))
print("Image shape:", image.shape)
