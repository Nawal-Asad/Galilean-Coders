
import io
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from astropy.io import fits
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.orbit import fetch_latest_tle, generate_ground_track, propagate_orbit
from backend.processing import compare_epochs
from spherex.config import CORS_ORIGINS, get_data_path, get_result_path, PROJECT_DIR

CANDIDATES_FILE = get_result_path("candidate_sources.csv")
DIFFERENCE_FILE = get_data_path("epoch2_minus_epoch1_difference.fits", processed=True)

# Known project FITS files for the FITS viewer
# Raw data files
FITS_CATALOG = {
    "epoch1.fits": ("Epoch 1 Reference Observation (Band D2 Level-2b)", "raw"),
    "epoch2.fits": ("Epoch 2 Comparison Observation (Band D2 Level-2b)", "raw"),
}
# Processed data files
FITS_CATALOG.update({
    "epoch2_aligned_to_epoch1.fits": ("Astrometrically Aligned Epoch 2 (Reprojected)", "processed"),
    "epoch2_minus_epoch1_difference.fits": ("Differential Image (Epoch 2 − Epoch 1)", "processed"),
    "epoch2_variance_aligned.fits": ("Aligned Variance Quality Map", "processed"),
    "epoch2_flags_aligned.fits": ("Aligned Pixel Quality Flags", "processed"),
    "epoch2_alignment_footprint.fits": ("Reprojection Coverage Footprint", "processed"),
})


# FastAPI application
app = FastAPI(
    title="SPHEREx Sky Explorer API",
    description="Backend API for comparing SPHEREx observations.",
    version="1.0.0",
)


# Frontend ko backend se connect karne ki permission
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "SPHEREx Sky Explorer backend is running",
        "status": "ok",
    }


# Do epochs ko compare karne ka endpoint
@app.get("/api/compare")
def compare():
    try:
        return compare_epochs()
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error))


# Candidate sources CSV se read karne ka endpoint
@app.get("/api/candidates")
def get_candidates(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    candidate_type: Literal["positive", "negative"] | None = None,
    min_abs_significance: float | None = Query(default=None, ge=0),
    sort_by: Literal["significance", "file"] = "significance",
):
    if type(limit) is not int:
        limit = 100
    if type(offset) is not int:
        offset = 0
    if candidate_type is not None:
        candidate_type = str(candidate_type).lower()
    if type(min_abs_significance) is not float and type(min_abs_significance) is not int and min_abs_significance is not None:
        min_abs_significance = None
    if sort_by is None:
        sort_by = "significance"

    if candidate_type not in (None, "positive", "negative"):
        raise HTTPException(status_code=422, detail="candidate_type must be 'positive', 'negative', or unset")
    if min_abs_significance is not None and min_abs_significance < 0:
        raise HTTPException(status_code=422, detail="min_abs_significance must be >= 0")
    if sort_by not in {"significance", "file"}:
        raise HTTPException(status_code=422, detail="sort_by must be 'significance' or 'file'")

    if not CANDIDATES_FILE.exists():
        raise HTTPException(
            status_code=404,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
            detail="Candidate CSV file not found",
        )

    try:
        stat = CANDIDATES_FILE.stat()
        df = _load_candidates(
            str(CANDIDATES_FILE),
            stat.st_mtime_ns,
            stat.st_size,
        ).copy()
    except (OSError, ValueError, pd.errors.ParserError) as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    if candidate_type is not None:
        df = df[df["type"] == candidate_type]

    if min_abs_significance is not None:
        df = df[df["significance"].abs() >= min_abs_significance]

    if sort_by == "significance":
        df = df.assign(_sort=df["significance"].abs())
        df = df.sort_values("_sort", ascending=False, kind="stable").drop(columns="_sort")

    total = len(df)
    selected = df.iloc[offset:offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results_are_validated_detections": False,
        "candidates": selected.to_dict(orient="records"),
    }


@lru_cache(maxsize=1)
def _load_candidates(file_path: str, modified_ns: int, file_size: int) -> pd.DataFrame:
    del modified_ns, file_size
    candidates = pd.read_csv(file_path)
    aliases = {
        "x": ("x", "x_pixel"),
        "y": ("y", "y_pixel"),
        "difference": ("difference",),
        "significance": ("significance", "significance_sigma"),
        "type": ("type",),
    }
    columns = {}
    for canonical, possible_names in aliases.items():
        source = next((name for name in possible_names if name in candidates.columns), None)
        if source is None:
            raise ValueError(f"Candidate CSV is missing the '{canonical}' column.")
        columns[canonical] = candidates[source]

    normalized = pd.DataFrame(columns)
    for column in ("x", "y", "difference", "significance"):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    valid_rows = (
        normalized[["x", "y", "difference", "significance"]]
        .apply(np.isfinite)
        .all(axis=1)
        & normalized["x"].mod(1).eq(0)
        & normalized["y"].mod(1).eq(0)
        & normalized["x"].ge(0)
        & normalized["y"].ge(0)
    )
    normalized["type"] = normalized["type"].astype(str).str.lower()
    valid_rows &= normalized["type"].isin(("positive", "negative"))
    if not valid_rows.all():
        raise ValueError(
            f"Candidate CSV contains {int((~valid_rows).sum())} invalid rows."
        )

    normalized["x"] = normalized["x"].astype("int64")
    normalized["y"] = normalized["y"].astype("int64")
    return normalized[["x", "y", "difference", "significance", "type"]]


@app.get("/api/cutout")
def get_candidate_cutout(
    x: int = Query(ge=0),
    y: int = Query(ge=0),
    radius: int = Query(default=20, ge=2, le=100),
):
    if x < 0 or y < 0:
        raise HTTPException(status_code=400, detail="Candidate coordinates must be non-negative")
    if radius < 2 or radius > 100:
        raise HTTPException(status_code=400, detail="radius must be between 2 and 100 pixels")

    if not DIFFERENCE_FILE.exists():
        raise HTTPException(status_code=404, detail="Difference image not found")

    try:
        with fits.open(DIFFERENCE_FILE, memmap=True) as hdul:
            image = hdul[0].data
            if image is None or image.ndim != 2:
                raise ValueError("Difference FITS file does not contain a 2D image.")
            height, width = image.shape
            if x >= width or y >= height:
                raise HTTPException(
                    status_code=400,
                    detail="Candidate coordinates are outside the difference image.",
                )
            x_min, x_max = max(0, x - radius), min(width, x + radius + 1)
            y_min, y_max = max(0, y - radius), min(height, y + radius + 1)
            cutout = np.array(image[y_min:y_max, x_min:x_max], dtype=np.float32)
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    finite_values = np.abs(cutout[np.isfinite(cutout)])
    display_limit = float(np.percentile(finite_values, 99)) if finite_values.size else 1.0
    if not np.isfinite(display_limit) or display_limit <= 0:
        display_limit = 1.0

    return {
        "x": x,
        "y": y,
        "radius": radius,
        "x_min": x_min,
        "y_min": y_min,
        "display_limit": display_limit,
        "difference": [
            [float(value) if np.isfinite(value) else None for value in row]
            for row in cutout
        ],
    }


# ==============================================================================
# Live Satellite Tracking Endpoints
# ==============================================================================

@app.get("/api/orbit/telemetry")
def get_orbit_telemetry():
    """Return real-time SPHEREx orbital state, position, and velocity."""
    try:
        return propagate_orbit()
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Orbit propagation error: {error}") from error


@app.get("/api/orbit/groundtrack")
def get_orbit_groundtrack(
    past_minutes: int = Query(default=45, ge=0, le=180),
    future_minutes: int = Query(default=95, ge=0, le=180),
    step_minutes: int = Query(default=1, ge=1, le=10),
):
    """Return ground track trajectory coordinates for current orbit pass."""
    try:
        track = generate_ground_track(
            start_offset_minutes=-past_minutes,
            end_offset_minutes=future_minutes,
            step_minutes=step_minutes,
        )
        return {
            "satellite": "SPHEREX (MIDEX 9)",
            "norad_id": 63182,
            "points": track,
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Ground track error: {error}") from error


@app.get("/api/orbit/tle")
def get_orbit_tle():
    """Return current TLE orbital elements for SPHEREx."""
    return fetch_latest_tle()


# ==============================================================================
# FITS Viewer Endpoints
# ==============================================================================

def _resolve_fits(filename: str) -> Path:
    """Resolve a FITS filename to its actual path in the new directory structure."""
    safe = Path(filename).name
    if safe not in FITS_CATALOG:
        raise HTTPException(status_code=404, detail=f"Unknown FITS file: {safe}")
    
    # Determine if file is raw or processed
    _, location = FITS_CATALOG[safe]
    path = get_data_path(safe, processed=(location == "processed"))
    
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"FITS file not found: {safe}")
    return path


@app.get("/api/fits/files")
def list_fits_files():
    """Return all available project FITS files and metadata."""
    files = []
    for name, (desc, location) in FITS_CATALOG.items():
        path = get_data_path(name, processed=(location == "processed"))
        files.append({
            "name": name,
            "description": desc,
            "exists": path.exists(),
            "size_mb": round(path.stat().st_size / (1024**2), 2) if path.exists() else 0.0,
        })
    return {"files": files}


@app.get("/api/fits/info")
def get_fits_info(file: str = Query(default="epoch1.fits")):
    """Return HDU overview and header metadata for a given FITS file."""
    path = _resolve_fits(file)
    try:
        with fits.open(path, memmap=True) as hdul:
            hdus = []
            for idx, h in enumerate(hdul):
                hdus.append({
                    "index": idx,
                    "name": h.name or f"HDU_{idx}",
                    "shape": list(h.data.shape) if h.data is not None else None,
                    "dtype": str(h.data.dtype) if h.data is not None else None,
                })

            # Target primary or image HDU
            target = hdul["IMAGE"] if "IMAGE" in hdul else hdul[0]
            header_cards = {
                k: str(v)
                for k, v in target.header.items()
                if k not in ("COMMENT", "HISTORY") and not k.startswith("---")
            }

            stats = None
            if target.data is not None:
                valid = target.data[np.isfinite(target.data)]
                if valid.size:
                    stats = {
                        "min": float(np.min(valid)),
                        "max": float(np.max(valid)),
                        "mean": float(np.mean(valid)),
                        "median": float(np.median(valid)),
                        "finite_pixels": int(valid.size),
                        "total_pixels": int(target.data.size),
                    }

            return {
                "file": file,
                "size_mb": round(path.stat().st_size / (1024**2), 2),
                "hdus": hdus,
                "header": header_cards,
                "stats": stats,
            }
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error reading FITS header: {error}") from error


@app.get("/api/fits/image")
def render_fits_image(
    file: str = Query(default="epoch1.fits"),
    hdu: str = Query(default="auto"),
    percentile_low: float = Query(default=1.0, ge=0.0, le=100.0),
    percentile_high: float = Query(default=99.5, ge=0.0, le=100.0),
    colormap: str = Query(default="inferno"),
):
    """Render a contrast-normalized PNG of a full 2D FITS image."""
    if percentile_low < 0 or percentile_high < 0 or percentile_high > 100 or percentile_low > 100:
        raise HTTPException(status_code=400, detail="Percentiles must be between 0 and 100")
    if percentile_high <= percentile_low:
        raise HTTPException(status_code=400, detail="percentile_high must be greater than percentile_low")

    path = _resolve_fits(file)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        with fits.open(path, memmap=True) as hdul:
            if hdu == "auto":
                target = hdul["IMAGE"] if "IMAGE" in hdul else hdul[0]
            elif hdu.isdigit():
                target = hdul[int(hdu)]
            else:
                target = hdul[hdu]

            data = np.asarray(target.data, dtype=np.float32).copy()

        if data.ndim != 2:
            raise HTTPException(status_code=400, detail="FITS HDU is not a 2D image.")

        valid = data[np.isfinite(data)]
        if valid.size == 0:
            raise HTTPException(status_code=400, detail="FITS image has no finite pixels.")

        if file == "epoch2_minus_epoch1_difference.fits":
            limit = float(np.percentile(np.abs(valid), percentile_high))
            if limit <= 0:
                limit = 1.0
            vmin, vmax = -limit, limit
        else:
            vmin = float(np.percentile(valid, percentile_low))
            vmax = float(np.percentile(valid, percentile_high))
            if vmax <= vmin:
                vmax = vmin + 1.0

        normalized = np.clip((data - vmin) / (vmax - vmin), 0.0, 1.0)
        cmap = plt.get_cmap(colormap if colormap in plt.colormaps() else "inferno")
        rgba = cmap(normalized, bytes=True)
        rgba[~np.isfinite(data)] = [10, 10, 14, 255]

        height, width = data.shape
        max_dimension = max(height, width)
        fig = plt.figure(
            figsize=(10 * width / max_dimension, 10 * height / max_dimension),
            dpi=120,
        )
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(rgba, origin="lower")
        ax.axis("off")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120)
        plt.close(fig)
        buf.seek(0)
        return Response(content=buf.read(), media_type="image/png")
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Image render failed: {error}") from error
