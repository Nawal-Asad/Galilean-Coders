import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path

from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io import fits

CSV_FILE = get_result_path("candidate_sources.csv")

df = pd.read_csv(CSV_FILE)

def read_image(filename):
    with fits.open(resolve_data_path(filename)) as hdul:
        for hdu in hdul:
            if hdu.data is not None and hdu.data.ndim == 2:
                return np.array(hdu.data, dtype=np.float32, copy=True)
    raise ValueError(f"No 2D image found: {filename}")

difference = read_image("epoch2_minus_epoch1_difference.fits")
footprint = read_image("epoch2_alignment_footprint.fits")

x = df["x"].to_numpy(dtype=int)
y = df["y"].to_numpy(dtype=int)

pixel_diff = difference[y, x]
pixel_footprint = footprint[y, x]

csv_diff = df["difference"].to_numpy(dtype=float)
csv_sig = df["significance"].to_numpy(dtype=float)

valid = (
    np.isfinite(pixel_diff)
    & np.isfinite(pixel_footprint)
    & (pixel_footprint > 0)
    & np.isfinite(csv_diff)
    & np.isfinite(csv_sig)
)

print("=== STEP 3: VALID CANDIDATE INVESTIGATION ===")
print("Total CSV records:", len(df))
print("Records with valid measurements and coverage:", int(valid.sum()))

print("\nValid candidates by type:")
print(df.loc[valid, "type"].value_counts().to_string())

print("\nDifference values for valid candidates:")
print(df.loc[valid, "difference"].describe().to_string())

print("\nAbsolute significance for valid candidates:")
print(df.loc[valid, "significance"].abs().describe().to_string())

print("\nSignificance thresholds among valid candidates:")
for threshold in [3, 5, 10, 20]:
    count = int((df.loc[valid, "significance"].abs() > threshold).sum())
    print(f"|significance| > {threshold}: {count}")

print("\nCoverage values for valid candidates:")
print(pd.Series(pixel_footprint[valid]).describe().to_string())

print("\nNo files were modified.")