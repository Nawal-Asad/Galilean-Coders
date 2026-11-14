import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import (
    ImageNormalize,
    PercentileInterval,
    AsinhStretch,
)

from spherex.config import get_data_path

epoch1_file = get_data_path("epoch1.fits")
aligned_file = get_data_path("epoch2_aligned_to_epoch1.fits", processed=True)
footprint_file = get_data_path("epoch2_alignment_footprint.fits", processed=True)

with fits.open(epoch1_file) as hdul:
    epoch1 = hdul["IMAGE"].data.astype(np.float32)

with fits.open(aligned_file) as hdul:
    epoch2 = hdul[0].data.astype(np.float32)

with fits.open(footprint_file) as hdul:
    footprint = hdul[0].data

print("Epoch 1 shape:", epoch1.shape)
print("Aligned Epoch 2 shape:", epoch2.shape)

valid = (
    np.isfinite(epoch1)
    & np.isfinite(epoch2)
    & np.isfinite(footprint)
    & (footprint > 0)
)

print("Valid comparison pixels:", np.count_nonzero(valid))

difference = np.full(epoch1.shape, np.nan, dtype=np.float32)
difference[valid] = epoch2[valid] - epoch1[valid]

print("Mean Epoch 1 brightness:", np.mean(epoch1[valid]))
print("Mean Epoch 2 brightness:", np.mean(epoch2[valid]))
print("Mean difference:", np.mean(difference[valid]))
print("Median difference:", np.median(difference[valid]))

output_file = get_data_path("epoch2_minus_epoch1_difference.fits", processed=True)

with fits.open(epoch1_file) as hdul:
    reference_header = hdul["IMAGE"].header.copy()

fits.PrimaryHDU(
    data=difference,
    header=reference_header
).writeto(output_file, overwrite=True)

print("Difference image saved:", output_file)

# Display both images using the same brightness scale
combined = np.concatenate([epoch1[valid], epoch2[valid]])
vmin, vmax = np.nanpercentile(combined, [1, 99.5])

fig, axes = plt.subplots(1, 3, figsize=(16, 6))

for ax, data, title in zip(
    axes[:2],
    [epoch1, epoch2],
    ["Epoch 1", "Epoch 2 aligned"]
):
    ax.imshow(
        np.where(valid, data, np.nan),
        origin="lower",
        cmap="inferno",
        vmin=vmin,
        vmax=vmax,
    )
    ax.set_title(title)
    ax.set_xlabel("X Pixel")
    ax.set_ylabel("Y Pixel")

diff_values = difference[valid]
limit = np.nanpercentile(np.abs(diff_values), 99)

if not np.isfinite(limit) or limit <= 0:
    limit = 1.0

im = axes[2].imshow(
    difference,
    origin="lower",
    cmap="coolwarm",
    vmin=-limit,
    vmax=limit,
)
axes[2].set_title("Epoch 2 - Epoch 1")
axes[2].set_xlabel("X Pixel")
axes[2].set_ylabel("Y Pixel")
fig.colorbar(im, ax=axes[2], label="Brightness difference (MJy / sr)")

plt.tight_layout()

plot_file = get_result_path("epoch_comparison.png")
plt.savefig(plot_file, dpi=150)
plt.show()

print("Comparison plot saved:", plot_file)
print("Comparison completed!")
