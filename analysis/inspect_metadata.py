

from astropy.io import fits

file_path = "epoch2.fits"

with fits.open(file_path) as hdul:
    header = hdul["IMAGE"].header

    print("=" * 45)
    print("SPHEREx EPOCH 2 — OBSERVATION METADATA")
    print("=" * 45)

    # Print important metadata if available
    keys_to_check = [
        "DATE-OBS",
        "MJD-OBS",
        "TELESCOP",
        "INSTRUME",
        "BUNIT",
        "FILTER",
        "WAVELNTH",
        "CRVAL1",
        "CRVAL2",
        "CTYPE1",
        "CTYPE2",
    ]

    for key in keys_to_check:
        if key in header:
            print(f"{key}: {header[key]}")
        else:
            print(f"{key}: Not present in IMAGE header")

    print("\nIMAGE dimensions:", hdul["IMAGE"].data.shape)

    print("\nAvailable HDU names:")
    for hdu in hdul:
        print(hdu.name)
