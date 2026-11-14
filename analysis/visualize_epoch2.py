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

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

fits_file = get_data_path("epoch2.fits")

with fits.open(fits_file) as hdul:
    image = hdul["IMAGE"].data.copy()

norm = ImageNormalize(
    image,
    interval=PercentileInterval(99.5),
    stretch=AsinhStretch(),
)

plt.figure(figsize=(10, 8))
plt.imshow(image, origin="lower", cmap="inferno", norm=norm)
plt.colorbar(label="Brightness (MJy / sr)")
plt.title("SPHEREx Epoch 2 — Sky Visualization")
plt.xlabel("X Pixel")
plt.ylabel("Y Pixel")
plt.tight_layout()

output_file = get_result_path("epoch2_visualization_enhanced.png")
plt.savefig(output_file, dpi=150)
plt.show()

print("Epoch 2 visualization saved to:", output_file)
