import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


import numpy as np
from astropy.io import fits

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

with fits.open(get_data_path("epoch1.fits")) as h1:
    flags1 = h1["FLAGS"].data.copy()
    variance1 = h1["VARIANCE"].data.copy()

with fits.open(get_data_path("epoch2_flags_aligned.fits", processed=True)) as h2:
    flags2 = h2[0].data.copy()

with fits.open(get_data_path("epoch2_variance_aligned.fits", processed=True)) as h2:
    variance2 = h2[0].data.copy()

print("Epoch 1 FLAGS:")
print("  SOURCE pixels:", np.sum((flags1 & 2097152) != 0))
print("  OVERFLOW pixels:", np.sum((flags1 & 2) != 0))
print("  TRANSIENT flag pixels:", np.sum((flags1 & 1) != 0))

print("\nEpoch 2 aligned FLAGS:")
valid_flags2 = flags2 >= 0
print("  Valid pixels:", np.sum(valid_flags2))
print("  SOURCE pixels:", np.sum(valid_flags2 & ((flags2 & 2097152) != 0)))
print("  OVERFLOW pixels:", np.sum(valid_flags2 & ((flags2 & 2) != 0)))
print("  TRANSIENT flag pixels:", np.sum(valid_flags2 & ((flags2 & 1) != 0)))

print("\nVariance comparison:")
valid1 = np.isfinite(variance1) & (variance1 > 0)
valid2 = np.isfinite(variance2) & (variance2 > 0)

print("  Epoch 1 positive variance pixels:", np.sum(valid1))
print("  Epoch 2 aligned positive variance pixels:", np.sum(valid2))
print("  Epoch 1 median variance:", np.nanmedian(variance1[valid1]))
print("  Epoch 2 median variance:", np.nanmedian(variance2[valid2]))
