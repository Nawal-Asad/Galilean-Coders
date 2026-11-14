"""
SPHEREx Real-Time Orbital Telemetry and Ground Track Engine.

Calculates real-time geodetic coordinates, orbital state vectors, and ground
tracks for the SPHEREx space telescope using NORAD satellite catalog ephemeris
(NORAD Cat ID 63182 / COSPAR 2025-047E).
"""

import datetime
import json
import math
import urllib.request
from typing import Any, Dict, List, Optional

# Astronomical and WGS-84 Geodetic Constants
MU = 398600.4418  # Earth gravitational parameter (km^3 / s^2)
R_EARTH = 6378.137  # WGS84 Earth equatorial radius (km)
J2 = 1.08263e-3  # Earth second zonal harmonic (oblateness)
OMEGA_EARTH = 7.2921159e-5  # Earth rotation rate (rad/s)

# Fallback official SPHEREx TLE (NORAD ID 63182)
DEFAULT_TLE = {
    "OBJECT_NAME": "SPHEREX (MIDEX 9)",
    "NORAD_CAT_ID": 63182,
    "OBJECT_ID": "2025-047E",
    "EPOCH": "2026-11-01T21:43:59.721312",
    "MEAN_MOTION": 14.74282824,  # revs per day
    "ECCENTRICITY": 0.00115262,
    "INCLINATION": 97.9577,  # degrees
    "RA_OF_ASC_NODE": 128.2467,  # degrees
    "ARG_OF_PERICENTER": 108.7772,  # degrees
    "MEAN_ANOMALY": 251.4688,  # degrees
    "BSTAR": 0.00010695684,
}

_cached_tle: Optional[Dict[str, Any]] = None
_cached_tle_time: float = 0.0


def fetch_latest_tle() -> Dict[str, Any]:
    """Fetch current TLE ephemeris from CelesTrak with 1-hour in-memory cache."""
    global _cached_tle, _cached_tle_time
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    if _cached_tle is not None and (now - _cached_tle_time) < 3600:
        return _cached_tle

    url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=63182&FORMAT=JSON"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SPHEREx-Sky-Explorer/1.0 (NASA Infrared Mission Tracker)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tle = data[0] if isinstance(data, list) else data
            if "MEAN_MOTION" in tle and "INCLINATION" in tle:
                _cached_tle = tle
                _cached_tle_time = now
                return tle
    except Exception:
        pass

    _cached_tle = DEFAULT_TLE
    _cached_tle_time = now
    return DEFAULT_TLE


def propagate_orbit(
    utc_dt: Optional[datetime.datetime] = None,
    tle: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate geodetic coordinates, velocity, and altitude for a given UTC timestamp."""
    if utc_dt is None:
        utc_dt = datetime.datetime.now(datetime.timezone.utc)
    if tle is None:
        tle = fetch_latest_tle()

    # Parse TLE Epoch
    epoch_str = tle.get("EPOCH", DEFAULT_TLE["EPOCH"])
    try:
        # Handle formats like 2026-11-01T21:43:59.721312
        if "T" in epoch_str:
            epoch = datetime.datetime.fromisoformat(epoch_str.replace("Z", "+00:00"))
            if epoch.tzinfo is None:
                epoch = epoch.replace(tzinfo=datetime.timezone.utc)
        else:
            epoch = datetime.datetime.now(datetime.timezone.utc)
    except Exception:
        epoch = datetime.datetime.now(datetime.timezone.utc)

    dt_sec = (utc_dt - epoch).total_seconds()

    n_rev_per_day = float(tle.get("MEAN_MOTION", DEFAULT_TLE["MEAN_MOTION"]))
    n_rad_per_sec = n_rev_per_day * 2.0 * math.pi / 86400.0
    a = (MU / (n_rad_per_sec**2)) ** (1.0 / 3.0)
    e = float(tle.get("ECCENTRICITY", DEFAULT_TLE["ECCENTRICITY"]))
    inc = math.radians(float(tle.get("INCLINATION", DEFAULT_TLE["INCLINATION"])))
    raan_0 = math.radians(float(tle.get("RA_OF_ASC_NODE", DEFAULT_TLE["RA_OF_ASC_NODE"])))
    arg_p_0 = math.radians(float(tle.get("ARG_OF_PERICENTER", DEFAULT_TLE["ARG_OF_PERICENTER"])))
    m_0 = math.radians(float(tle.get("MEAN_ANOMALY", DEFAULT_TLE["MEAN_ANOMALY"])))

    # J2 nodal precession (Sun-synchronous nodal precession rate)
    raan_dot = -1.5 * n_rad_per_sec * J2 * (R_EARTH / a) ** 2 * math.cos(inc)
    raan = raan_0 + raan_dot * dt_sec

    # Argument of pericenter precession
    arg_p_dot = 0.75 * n_rad_per_sec * J2 * (R_EARTH / a) ** 2 * (5.0 * (math.cos(inc) ** 2) - 1.0)
    arg_p = arg_p_0 + arg_p_dot * dt_sec

    # Mean anomaly propagation
    m = (m_0 + n_rad_per_sec * dt_sec) % (2.0 * math.pi)

    # Solve Kepler's equation for eccentric anomaly E
    E = m
    for _ in range(12):
        f = E - e * math.sin(E) - m
        f_prime = 1.0 - e * math.cos(E)
        if abs(f_prime) < 1e-12:
            break
        delta = f / f_prime
        E -= delta
        if abs(delta) < 1e-9:
            break

    nu = 2.0 * math.atan2(
        math.sqrt(1.0 + e) * math.sin(E / 2.0),
        math.sqrt(1.0 - e) * math.cos(E / 2.0),
    )
    r = a * (1.0 - e * math.cos(E))

    # Orbital plane coordinates
    u = arg_p + nu
    x_orb = r * math.cos(u)
    y_orb = r * math.sin(u)

    # Convert to Earth-Centered Inertial (ECI) coordinates
    x_eci = x_orb * math.cos(raan) - y_orb * math.cos(inc) * math.sin(raan)
    y_eci = x_orb * math.sin(raan) + y_orb * math.cos(inc) * math.cos(raan)
    z_eci = y_orb * math.sin(inc)

    # Greenwich Mean Sidereal Time (GMST)
    jd = (utc_dt.timestamp() / 86400.0) + 2440587.5
    d = jd - 2451545.0
    gmst_deg = (280.46061837 + 360.98564736629 * d) % 360.0
    gmst_rad = math.radians(gmst_deg)

    # Convert to Earth-Centered Earth-Fixed (ECEF) coordinates
    x_ecef = x_eci * math.cos(gmst_rad) + y_eci * math.sin(gmst_rad)
    y_ecef = -x_eci * math.sin(gmst_rad) + y_eci * math.cos(gmst_rad)
    z_ecef = z_eci

    # Sub-satellite Latitude, Longitude, Altitude
    lon = math.degrees(math.atan2(y_ecef, x_ecef))
    # Normalize longitude to [-180, +180]
    lon = ((lon + 180.0) % 360.0) - 180.0

    p = math.sqrt(x_ecef**2 + y_ecef**2)
    lat = math.degrees(math.atan2(z_ecef, p))
    alt = r - R_EARTH
    vel = math.sqrt(MU * (2.0 / r - 1.0 / a))

    # Sub-solar point for day/night illumination
    # Approximate solar coordinates
    n_days = d
    sun_L = (280.460 + 0.9856474 * n_days) % 360.0
    sun_g = math.radians((357.528 + 0.9856003 * n_days) % 360.0)
    sun_lambda = math.radians(sun_L + 1.915 * math.sin(sun_g) + 0.020 * math.sin(2 * sun_g))
    sun_eps = math.radians(23.439 - 0.0000004 * n_days)
    sun_ra = math.atan2(math.cos(sun_eps) * math.sin(sun_lambda), math.cos(sun_lambda))
    sun_dec = math.asin(math.sin(sun_eps) * math.sin(sun_lambda))
    sun_lon = ((math.degrees(sun_ra - gmst_rad) + 180.0) % 360.0) - 180.0
    sun_lat = math.degrees(sun_dec)

    # Angular distance to sun to determine eclipse / daylight
    sat_vec = [x_ecef / r, y_ecef / r, z_ecef / r]
    sun_x = math.cos(sun_dec) * math.cos(math.radians(sun_lon))
    sun_y = math.cos(sun_dec) * math.sin(math.radians(sun_lon))
    sun_z = math.sin(sun_dec)
    dot = sat_vec[0] * sun_x + sat_vec[1] * sun_y + sat_vec[2] * sun_z
    in_sunlight = dot > -0.2  # slight grazing allowance

    # Ground footprint horizon radius in kilometers
    footprint_radius_km = math.acos(R_EARTH / max(r, R_EARTH + 1.0)) * R_EARTH

    return {
        "timestamp": utc_dt.isoformat(),
        "norad_id": tle.get("NORAD_CAT_ID", 63182),
        "satellite": tle.get("OBJECT_NAME", "SPHEREX (MIDEX 9)"),
        "international_designator": tle.get("OBJECT_ID", "2025-047E"),
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "altitude_km": round(alt, 2),
        "velocity_kms": round(vel, 3),
        "velocity_kmh": round(vel * 3600.0, 1),
        "orbital_period_minutes": round((2.0 * math.pi / n_rad_per_sec) / 60.0, 2),
        "orbital_inclination_deg": round(math.degrees(inc), 3),
        "footprint_radius_km": round(footprint_radius_km, 1),
        "in_sunlight": in_sunlight,
        "subsolar_point": {
            "latitude": round(sun_lat, 3),
            "longitude": round(sun_lon, 3),
        },
        "orbit_regime": "Sun-Synchronous Polar Orbit (SSO)",
    }


def generate_ground_track(
    start_offset_minutes: int = -45,
    end_offset_minutes: int = 95,
    step_minutes: int = 1,
) -> List[Dict[str, Any]]:
    """Compute orbital ground track coordinates for past and future passes."""
    if step_minutes <= 0:
        raise ValueError("step_minutes must be a positive integer")

    now = datetime.datetime.now(datetime.timezone.utc)
    tle = fetch_latest_tle()
    track: List[Dict[str, Any]] = []

    for offset in range(start_offset_minutes, end_offset_minutes + 1, step_minutes):
        t = now + datetime.timedelta(minutes=offset)
        pos = propagate_orbit(t, tle)
        track.append({
            "offset_minutes": offset,
            "timestamp": pos["timestamp"],
            "latitude": pos["latitude"],
            "longitude": pos["longitude"],
            "altitude_km": pos["altitude_km"],
            "is_past": offset < 0,
            "is_current": offset == 0,
        })

    return track
