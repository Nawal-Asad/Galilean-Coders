import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path


from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io import fits


def read_image(filename, ext=0):
    with fits.open(resolve_data_path(filename)) as hdul:
        return np.array(hdul[ext].data, copy=True)

df = pd.read_csv(get_result_path("candidate_sources.csv"))

with fits.open(get_data_path("epoch1.fits")) as hdul:
    epoch1 = np.array(hdul["IMAGE"].data, copy=True)
    flags1 = np.array(hdul["FLAGS"].data, copy=True)

epoch2 = read_image("epoch2_aligned_to_epoch1.fits")
flags2 = read_image("epoch2_flags_aligned.fits")
diff = read_image("epoch2_minus_epoch1_difference.fits")
footprint = read_image("epoch2_alignment_footprint.fits")

x = df["x"].to_numpy(dtype=int)
y = df["y"].to_numpy(dtype=int)

valid = (
    np.isfinite(epoch1[y, x])
    & np.isfinite(epoch2[y, x])
    & np.isfinite(diff[y, x])
    & (footprint[y, x] > 0)
    & np.isfinite(df["significance"].to_numpy(dtype=float))
    & np.isfinite(df["difference"].to_numpy(dtype=float))
)

x, y = x[valid], y[valid]
print("Valid candidates:", len(x))

flag_names = {
    0: "TRANSIENT",
    1: "OVERFLOW",
    2: "SUR_ERROR",
    4: "PHANTOM",
    5: "REFERENCE",
    6: "NONFUNC",
    7: "DICHROIC",
    9: "MISSING_DATA",
    10: "HOT",
    11: "COLD",
    12: "FULLSAMPLE",
    14: "PHANMISS",
    15: "NONLINEAR",
    17: "PERSIST",
    19: "OUTLIER",
    21: "SOURCE",
    22: "GHOST",
    23: "GHOST_FPA",
    24: "GHOST_EXT",
    26: "BLOOM",
    27: "SNOWBALL",
    28: "HALO",
}

print("\n=== EPOCH 1 FLAG COUNTS ===")
for bit, name in flag_names.items():
    count = int(np.count_nonzero(flags1[y, x] & (1 << bit)))
    if count:
        print(f"{name}: {count}")

print("\n=== ALIGNED EPOCH 2 FLAG COUNTS ===")
for bit, name in flag_names.items():
    count = int(np.count_nonzero(flags2[y, x] & (1 << bit)))
    if count:
        print(f"{name}: {count}")

print("\nNo files were modified.")
