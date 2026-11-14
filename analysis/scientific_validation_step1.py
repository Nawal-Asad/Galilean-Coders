import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path


from pathlib import Path
import numpy as np
import pandas as pd

CSV_FILE = get_result_path("candidate_sources.csv")

IMAGE_HEIGHT = 2040
IMAGE_WIDTH = 2040

if not CSV_FILE.exists():
    raise FileNotFoundError(f"CSV not found: {CSV_FILE}")

df = pd.read_csv(CSV_FILE)

required_columns = {
    "x", "y", "difference", "significance", "type"
}

missing = required_columns - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {sorted(missing)}")

print("\n=== STEP 1: CANDIDATE DATA AUDIT ===")

print("\nTotal records:", len(df))
print("Columns:", df.columns.tolist())

print("\nMissing values:")
print(df[list(required_columns)].isna().sum())

print("\nDuplicate coordinates:", df.duplicated(["x", "y"]).sum())

print("\nCandidate types:")
print(df["type"].value_counts(dropna=False))

print("\nCoordinate ranges:")
print("X:", df["x"].min(), "to", df["x"].max())
print("Y:", df["y"].min(), "to", df["y"].max())

inside_image = (
    df["x"].between(0, IMAGE_WIDTH - 1)
    & df["y"].between(0, IMAGE_HEIGHT - 1)
)

print("\nCandidates inside image:", int(inside_image.sum()))
print("Candidates outside image:", int((~inside_image).sum()))

finite = np.isfinite(
    df[["difference", "significance"]].to_numpy(dtype=float)
).all(axis=1)

print("\nRecords with finite measurements:", int(finite.sum()))
print("Records with non-finite measurements:", int((~finite).sum()))

print("\nSignificance distribution:")
print(df["significance"].describe(percentiles=[
    0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99
]))

sig = df["significance"].to_numpy(dtype=float)
sig = sig[np.isfinite(sig)]

print("\nAbsolute significance thresholds:")
for threshold in [3, 5, 10, 20]:
    print(
        f"|significance| > {threshold}:",
        int((np.abs(sig) > threshold).sum())
    )

print("\nCandidates near image edges:")
for border in [10, 25, 50]:
    near_edge = (
        (df["x"] < border)
        | (df["x"] >= IMAGE_WIDTH - border)
        | (df["y"] < border)
        | (df["y"] >= IMAGE_HEIGHT - border)
    )
    print(f"Within {border} pixels of an edge:", int(near_edge.sum()))

print("\nDifference distribution:")
print(df["difference"].describe())

print("\nAudit complete. Original CSV was not modified.")
