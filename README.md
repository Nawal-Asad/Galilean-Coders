# SPHEREx Sky Explorer

This project includes a Flask mission-information site, a FastAPI data API, and
scripts for aligning and comparing SPHEREx FITS observations.

## Project layout

- `data/raw/` - original epoch FITS observations.
- `data/processed/` - aligned images, difference images, variance, flags, and
  reprojection footprints.
- `results/` - candidate catalogues and generated plots.
- `spherex/` - central path configuration used by the applications and scripts.
- `scripts/` - pipeline execution modules.
- `analysis/` - validation, inspection, checking, and visualization modules.
- `backend/` and `frontend/` - FastAPI and Flask application components.
- `tests/` - automated tests.

## Setup

Run these commands from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and adjust the settings for your machine or
hosting environment. The application loads `.env` automatically; environment
variables already supplied by a hosting platform take precedence.

For a new local setup, create the private configuration file without
overwriting an existing one:

```bash
cp -n .env.example .env
```

- `HOST` and `PORT` control the application listener. Hosting platforms
  typically require `HOST=0.0.0.0` and provide `PORT` themselves.
- `SPHEREX_DATA_DIR` sets the directory containing `raw/` and `processed/`.
- `SPHEREX_RESULTS_DIR` sets the candidate catalogue and results directory.
- `SPHEREX_CORS_ORIGINS` is a comma-separated list of browser origins allowed
  to access the API. Set it to your public website origin if the frontend and
  API are hosted on different domains.

Data and results paths may be absolute paths on persistent storage, which
helps keep large FITS files separate from replaceable application code. Do not
commit `.env`; keep secrets out of `.env.example`.

## Process the observations

Place `epoch1.fits` and `epoch2.fits` in `data/raw/`, then run:

```bash
python -m scripts.align_epochs
python -m scripts.align_quality_maps
python -m scripts.compare_aligned_images
python -m scripts.detect_candidates
```

The final command writes the canonical candidate catalogue to
`results/candidate_sources.csv`. The API reads this same file, so rerunning candidate
detection updates the data shown in the explorer. The previous
`results/improved_candidate_sources.csv` file is retained unchanged as a legacy
analysis output and is not used by the API; it contains rows that fail the
current finite-value checks and should not be treated as a valid catalogue.

The pipeline modules can also be run directly, for example:

```bash
python scripts/align_epochs.py
```

## Run the application

### Option 1: Single command (Recommended — Unified on one URL)

Start both frontend and backend together under a single URL with one command:

```bash
./start.sh
```

Or using Python directly:

```bash
.venv/bin/python unified_app.py
```

Open your browser to:
- **Landing Page**: <http://127.0.0.1:8000>
- **Data Explorer**: <http://127.0.0.1:8000/explorer>
- **Live Satellite Tracker**: <http://127.0.0.1:8000/tracker> (Real-time SPHEREx orbit & ground track)
- **FITS Image Viewer**: <http://127.0.0.1:8000/fits> (Contrast stretch, colormaps, header explorer)
- **API Documentation**: <http://127.0.0.1:8000/docs>
- **API Health Check**: <http://127.0.0.1:8000/api>

Press `Ctrl+C` to cleanly stop the server.

To customize the port or host:
```bash
PORT=8080 ./start.sh
HOST=0.0.0.0 ./start.sh
```

`start.sh` also reads the default `HOST` and `PORT` from `.env`. On a hosting
platform, prefer its process manager and configured environment variables
rather than running the development server from a terminal.

### Option 2: Run services separately (Dual-process Mode)

You can also run both services as separate processes with `./start.sh --dual`, or start them in separate terminals:

Terminal 1 (FastAPI backend):
```bash
.venv/bin/python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 (Flask frontend):
```bash
.venv/bin/python -m frontend.app
```

Open the landing page at <http://127.0.0.1:5000>, the Data Explorer at
<http://127.0.0.1:5000/explorer>, and the API documentation at
<http://127.0.0.1:8000/docs>. If port 5000 is occupied, set a port when starting
Flask with:

```bash
.venv/bin/python -c 'from frontend.app import app; app.run(host="127.0.0.1", port=5001)'
```

The Data Explorer compares the Epoch 1 reference image, Epoch 2 aligned to the
Epoch 1 pixel grid, and their difference image. Candidate markers are shown on
all three views and match the current candidate-table page; selecting a marker
or candidate opens its difference-image cutout and exact image-pixel
coordinates. These are candidates detected in the difference image, not
independently detected sources in each epoch. Candidate significance is
exploratory; candidates are not confirmed detections. In particular, the
variance map is reprojected onto the reference grid, so the statistical effect
of resampling must be calibrated before the displayed significance can be
interpreted as a scientifically reliable false-alarm probability. The current
Explorer reports image-pixel coordinates, not sky coordinates.

## Tests

Run the backend, candidate-generation, and frontend route tests with:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

If pytest is installed, the same suite can be run with:

```bash
.venv/bin/python -m pytest tests/ -v
```
