
from astropy.io import fits

files = ["epoch1.fits", "epoch2.fits"]

for filename in files:
    print(f"\n{'=' * 50}")
    print("FILE:", filename)

    with fits.open(filename) as hdul:
        for name in ["IMAGE", "FLAGS", "VARIANCE"]:
            if name not in hdul:
                print(f"{name}: NOT FOUND")
                continue

            hdu = hdul[name]
            header = hdu.header

            print(f"\nExtension: {name}")
            print("Shape:", hdu.data.shape if hdu.data is not None else None)

            for key in [
                "CTYPE1", "CTYPE2",
                "CRPIX1", "CRPIX2",
                "CRVAL1", "CRVAL2",
                "CDELT1", "CDELT2",
                "CD1_1", "CD1_2",
                "CD2_1", "CD2_2"
            ]:
                if key in header:
                    print(f"{key}: {header[key]}")
