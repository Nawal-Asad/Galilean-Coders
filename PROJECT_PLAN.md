# SPHEREx Sky Explorer — Master Architecture & Project Plan

**Project:** SPHEREx Sky Explorer  
**Platform:** Unified Python Application (FastAPI + Flask on Uvicorn)  
**Primary Entrypoint:** `./start.sh` (or `python unified_app.py`) at `http://127.0.0.1:8000`  
**Target Capabilities:**
1. **Live Satellite Tracking** (Real-time SPHEREx orbital telemetry & ground track via NORAD 63182)
2. **Dedicated FITS Viewer** (Interactive astronomical image display, stretch, colormaps, header explorer)
3. **Directory Organization** (Clean separation of raw data, processed assets, analysis, and web modules)

---

## 1. Live Satellite Tracking for SPHEREx

### 1.1 Astronomical & Orbital Identification
SPHEREx is tracked in public satellite catalogs under:
- **Object Name:** `SPHEREX (MIDEX 9)`
- **NORAD Catalog ID:** `63182`
- **COSPAR / International ID:** `2025-047E`
- **Orbit Classification:** Low Earth Sun-Synchronous Polar Orbit (SSO)
- **Mean Motion:** ~14.74 revolutions per day (~97.6 minute orbital period)
- **Inclination:** ~97.96°
- **Altitude:** ~700 km

### 1.2 System Architecture
```
                  [ CelesTrak / NORAD API ]
                             │
                             ▼ (Cached Hourly)
              [ Backend: /api/orbit/telemetry ]
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
    [ Real-Time Propagation ]    [ SGP4 / Ground Track ]
    • Lat, Lon, Altitude, Vel    • Past & Future Orbit Path
    • Day/Night Terminator       • Next Ground Passes
                 │                       │
                 └───────────┬───────────┘
                             ▼
              [ Frontend: /tracker or /orbit ]
             Interactive 3D Earth Globe + 2D Map
```

### 1.3 Backend Implementation
- **Module:** `backend/orbit.py`
- **Endpoints:**
  - `GET /api/orbit/tle`: Returns latest cached TLE ephemeris for NORAD ID 63182.
  - `GET /api/orbit/telemetry`: Computes instantaneous sub-satellite coordinates (Latitude, Longitude, Altitude in km, Velocity in km/s, footprint diameter, daylight/eclipse state).
  - `GET /api/orbit/groundtrack`: Computes ground track path for ±1 orbit (~97 minutes).
- **Resilience:** If network is unreachable, fallback to high-fidelity analytical Keplerian state with the official baseline orbital elements.

### 1.4 Frontend Presentation
- **Route:** `/tracker` (with embedded widget on the landing page `/`).
- **Features:**
  - **Live Telemetry HUD:** Altitude, Orbital Speed, Latitude/Longitude, Sun elevation, Rev counter.
  - **Interactive 3D Orbit Globe:** Earth with day/night illumination, satellite model/marker, orbital ring, and sun direction.
  - **Ground Track 2D Projection:** Equirectangular world map showing the current ground position and upcoming orbital strip scans.

---

## 2. Dedicated FITS Viewer Plan

### 2.1 Supported Observations & Products
- `epoch1.fits`: Raw Level-2b reference observation (Band D2).
- `epoch2.fits`: Raw Level-2b second epoch observation.
- `epoch2_aligned_to_epoch1.fits`: Astrometrically reprojected Epoch 2 on Epoch 1 WCS.
- `epoch2_minus_epoch1_difference.fits`: Differential science image (Epoch 2 − Epoch 1).
- `epoch2_variance_aligned.fits`: Propagated error variance map.
- `epoch2_flags_aligned.fits`: Bitmask quality flags (bad pixels, overflow, cosmic rays).
- `epoch2_alignment_footprint.fits`: Geometric overlap footprint.

### 2.2 Backend Image Rendering & Metadata Engine
- **Endpoints:**
  - `GET /api/fits/files`: Enumerate available FITS files and their file sizes.
  - `GET /api/fits/info?file=<name>&hdu=<index>`: Returns dimensions, BUNIT, dynamic range stats (min/max/median/std), and header keywords.
  - `GET /api/fits/image?file=<name>&hdu=...&stretch=...&pmin=...&pmax=...&cmap=...`: Generates contrast-stretched PNG for instant web rendering.
  - `GET /api/fits/region?file=<name>&x=...&y=...&radius=...`: High-resolution pixel cutout around a selected focal plane coordinate.
  - `GET /api/fits/pixel?file=<name>&x=...&y=...`: Hover query returning exact pixel flux, flag breakdown, and celestial RA/Dec coordinates.

### 2.3 User Interface (`/fits`)
- **Control Bar:** File selector, HDU selector, Stretch dropdown (Asinh, Percentile 99.5%, Linear, Log), Colormap picker (Inferno, Magma, Coolwarm, Grayscale).
- **Viewport:** Zoomable, draggable viewport with reticle crosshair.
- **Inspector Panel:**
  - Dynamic pixel readouts: `(X, Y) -> RA (hms), Dec (dms) | Flux (MJy/sr)`.
  - Header inspection table with real-time keyword search (e.g. `CTYPE`, `CRVAL`, `DATE-OBS`).

---

## 3. Directory & File Organization Plan

Currently, several generated files and analysis scripts sit in the root folder alongside raw FITS files (~240 MB). The target layout will keep the repository organized and maintainable:

```
SphereX/
├── README.md                           # Documentation & quickstart
├── PROJECT_PLAN.md                     # Architecture, orbit tracking, & roadmap
├── requirements.txt                    # Project dependencies
├── start.sh                            # Single-command executable launcher
├── unified_app.py                      # Combined FastAPI + Flask ASGI app
│
├── data/                               # Data storage (git-ignored for big files)
│   ├── raw/                            # Raw mission FITS files (epoch1.fits, epoch2.fits)
│   └── processed/                      # Aligned images, variance, difference FITS
│
├── results/                            # Pipeline outputs
│   ├── candidate_sources.csv           # Canonical candidate catalog
│   └── plots/                          # Diagnostic charts and visualizations
│
├── backend/                            # FastAPI backend services
│   ├── main.py                         # API routes (/api/compare, /api/candidates, /api/cutout)
│   ├── processing.py                   # Astrometric comparison & stats logic
│   └── orbit.py                        # SPHEREx live orbital telemetry & TLE engine
│
├── frontend/                           # Flask web frontend
│   ├── app.py                          # Route controller (/, /explorer, /fits, /tracker)
│   ├── static/                         # Static CSS, JS, and image assets
│   └── templates/                      # Jinja2 HTML templates
│       ├── index.html                  # 3D Mission Landing Page
│       ├── explorer.html               # Data Explorer & Candidate Inspector
│       ├── fits_viewer.html            # Dedicated FITS Display & Header Inspector
│       └── tracker.html                # Live Satellite Orbit & Telemetry HUD
│
├── scripts/                            # Pipeline execution scripts
│   ├── align_epochs.py                 # Astrometric reprojection
│   ├── align_quality_maps.py           # Flags & variance reprojection
│   ├── compare_aligned_images.py       # Difference image computation
│   └── detect_candidates.py            # Transient & variable candidate detection
│
├── analysis/                           # Scientific validation & exploration scripts
│   ├── check_wcs.py
│   ├── check_quality_flags.py
│   └── validate_detection.py
│
└── tests/                              # Automated test suite
    ├── test_backend.py                 # Comparison & candidate tests
    ├── test_frontend.py                # Flask route tests
    ├── test_unified.py                 # ASGI integration tests
    └── test_orbit.py                   # Live orbit propagation tests
```

---

## 4. Implementation Schedule

| Phase | Milestone | Deliverable |
| :--- | :--- | :--- |
| **Phase 1** | **Architecture Documentation** | `PROJECT_PLAN.md` created with full specifications. |
| **Phase 2** | **Live Tracking Module** | `backend/orbit.py` with real-time TLE propagation (NORAD 63182) and `/api/orbit/*` endpoints. |
| **Phase 3** | **FITS Display Service** | `/api/fits/*` endpoints and `/fits` interactive viewer template. |
| **Phase 4** | **Tracking Frontend** | Live 3D globe / 2D map tracker template and navigation integration. |
| **Phase 5** | **File Organization** | Path resolver ensuring all scripts work seamlessly with organized folders. |
| **Phase 6** | **Verification & Tests** | Comprehensive test execution with single-command validation (`./start.sh`). |
