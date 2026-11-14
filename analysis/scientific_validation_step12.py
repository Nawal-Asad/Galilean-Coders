import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path


from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io import fits


df = pd.read_csv(get_result_path("candidate_sources.csv"))

def read_image(filename, ext=0):
    with fits.open(resolve_data_path(filename)) as hdul:
        return np.array(hdul[ext].data, copy=True)

epoch1 = read_image("epoch1.fits", "IMAGE")
flags1 = read_image("epoch1.fits", "FLAGS")
flags2 = read_image("epoch2_flags_aligned.fits")
diff = read_image("epoch2_minus_epoch1_difference.fits")
footprint = read_image("epoch2_alignment_footprint.fits")

x = df["x"].to_numpy(dtype=int)
y = df["y"].to_numpy(dtype=int)

difference = df["difference"].to_numpy(dtype=float)
significance = df["significance"].to_numpy(dtype=float)

valid = (
    np.isfinite(epoch1[y, x])
    & np.isfinite(diff[y, x])
    & (footprint[y, x] > 0)
    & np.isfinite(difference)
    & np.isfinite(significance)
)

flag1 = flags1[y, x]
flag2 = flags2[y, x]

# Flags needing extra investigation, not automatic proof of a false detection.
problem_bits = [0, 1, 2, 4, 6, 9, 10, 11, 14, 15, 17, 19, 22, 23, 24, 26, 27, 28]

problem_mask = 0
for bit in problem_bits:
    problem_mask |= 1 << bit

has_quality_flags = (
    ((flag1 & problem_mask) != 0)
    | ((flag2 & problem_mask) != 0)
)

clean_for_review = valid & ~has_quality_flags
flagged_for_review = valid & has_quality_flags

print("=== STEP 12: CANDIDATE REVIEW ===")
print("Total CSV rows:", len(df))
print("Valid measurable candidates:", int(valid.sum()))
print("Candidates with review flags:", int(flagged_for_review.sum()))
print("Candidates without selected review flags:", int(clean_for_review.sum()))

print("\n=== SIGNIFICANCE AMONG VALID CANDIDATES ===")
for threshold in [3, 5, 10, 20]:
    count = int(np.count_nonzero(valid & (np.abs(significance) >= threshold)))
    print(f"|significance| >= {threshold}: {count}")

print("\nNote: These are preliminary review groups, not confirmed detections.")
print("No files were modified.")
