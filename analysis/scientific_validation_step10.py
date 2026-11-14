import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spherex.config import get_result_path, resolve_data_path


from pathlib import Path
import numpy as np
from astropy.io import fits


FLAG_BITS = {
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

def read_flags(filename, ext=2):
    with fits.open(resolve_data_path(filename)) as hdul:
        return np.array(hdul[ext].data, copy=True)

def decode(value):
    value = int(value)
    names = [
        name for bit, name in FLAG_BITS.items()
        if value & (1 << bit)
    ]
    known_mask = sum(1 << bit for bit in FLAG_BITS)
    unknown_bits = value & ~known_mask
    if unknown_bits:
        names.append(f"UNMAPPED_BITS={unknown_bits}")
    return names or ["No mapped flags"]

epoch1_flags = read_flags("epoch1.fits")
epoch2_flags = read_flags("epoch2_flags_aligned.fits", ext=0)

coordinates = [
    (1618, 247), (557, 598), (1340, 168),
    (35, 1401), (774, 780), (654, 1770)
]

print("=== STEP 10: DECODED FLAGS ===")

for x, y in coordinates:
    print(f"\nPixel (x={x}, y={y})")
    print("Epoch 1 flags:", decode(epoch1_flags[y, x]))
    print("Aligned Epoch 2 flags:", decode(epoch2_flags[y, x]))

print("\nNo files were modified.")
