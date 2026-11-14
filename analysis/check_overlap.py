import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

from spherex.config import PROJECT_DIR, get_data_path, get_result_path

files = {
    "Epoch 1": get_data_path("epoch1.fits"),
    "Epoch 2": get_data_path("epoch2.fits"),
}

wcs_data = {}

for name, path in files.items():
    with fits.open(path) as hdul:
        image = hdul["IMAGE"].data
        wcs = WCS(hdul["IMAGE"].header).celestial
        wcs_data[name] = (wcs, image.shape)

def perimeter(shape, samples=300):
    ny, nx = shape
    t = np.linspace(0, 1, samples, endpoint=False)

    x = np.concatenate([
        t * (nx - 1),
        np.full(samples, nx - 1),
        (1 - t) * (nx - 1),
        np.zeros(samples)
    ])

    y = np.concatenate([
        np.zeros(samples),
        t * (ny - 1),
        np.full(samples, ny - 1),
        (1 - t) * (ny - 1)
    ])

    return x, y

def points_inside(source, target):
    source_wcs, source_shape = wcs_data[source]
    target_wcs, target_shape = wcs_data[target]

    x, y = perimeter(source_shape)
    sky = source_wcs.pixel_to_world(x, y)
    tx, ty = target_wcs.world_to_pixel(sky)

    ny, nx = target_shape
    boundary_inside = (
        (tx >= 0) & (tx < nx) &
        (ty >= 0) & (ty < ny)
    )

    # Also test the source image center.
    cx, cy = (source_shape[1] - 1) / 2, (source_shape[0] - 1) / 2
    center_sky = source_wcs.pixel_to_world(cx, cy)
    px, py = target_wcs.world_to_pixel(center_sky)

    center_inside = 0 <= px < nx and 0 <= py < ny

    return np.count_nonzero(boundary_inside), center_inside

for source, target in [
    ("Epoch 1", "Epoch 2"),
    ("Epoch 2", "Epoch 1")
]:
    count, center = points_inside(source, target)
    print(f"\n{source} checked against {target}")
    print("Boundary samples inside target:", count)
    print("Source center inside target:", center)

print("\nCheck completed. Boundary sampling is an overlap test,")
print("not an exact measurement of overlap area.")
