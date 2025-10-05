"""Observation builder for RL agent.

Replicates (in reduced form) the ordering used in the training environment
(`microgrid_env.MicrogridEMSEnv._get_observation`). Where real data is not yet
available in the operational backend, reasonable placeholders are inserted so
that the produced vector length matches the original observation dimension.

This allows us to (a) ship a full-length feature vector to the RL service so
its normalization stats remain meaningful, and (b) progressively replace
placeholders with live data sources (forecasts, multi‑battery telemetry,
market price feed, EV fleet state, etc.) without changing downstream code.

NOTE: All values are already scaled consistently with the training env:
 - Temporal: hour/24, minute/60, day_of_week/7, is_weekend (0/1)
 - Prices divided by 100 (mirrors env logic)
 - Temperatures /50
 - Power limits normalised to 1 (placeholders) pending dynamic derivation.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Dict, Any

from .database import SessionLocal
from . import crud

# Static mirrors of env_config (lightweight; we avoid importing training code)
FORECAST_HORIZON_STEPS = 8
BATTERY_COUNT = 2

def _now() -> datetime:
    return datetime.now(timezone.utc)

def build_observation(device_id: str) -> List[float]:
    """Build a full-length observation vector for the RL model.

    Currently uses a single device telemetry row and fans out to the two
    battery slots expected by the trained policy. Second battery is a
    placeholder until multi‑battery telemetry ingestion is implemented.
    """
    db = SessionLocal()
    latest = crud.latest_telemetry(db, device_id)
    db.close()

    # --- Temporal features ---
    now = _now()
    hour = now.hour / 24.0
    minute = now.minute / 60.0
    day_of_week = now.weekday() / 7.0
    is_weekend = 1.0 if now.weekday() >= 5 else 0.0
    obs: List[float] = [hour, minute, day_of_week, is_weekend]

    # Helper placeholders (will be replaced by real services later)
    # Simple diurnal shaped PV / wind heuristic for current value
    import math
    solar_profile = max(0.0, math.sin((now.hour - 6) / 12 * math.pi))  # 0..1
    wind_profile = 0.5 + 0.3 * math.sin(now.hour / 24 * 2 * math.pi)
    pv_current = 3200 * solar_profile  # kW scaled to training capacity
    wt_current = 2500 * wind_profile

    def repeat(v: float, n: int) -> List[float]:
        return [v for _ in range(n)]

    # Forecast & history placeholders (copy current with tiny variation)
    pv_forecast = [pv_current * (1 + 0.02 * (i+1)) for i in range(FORECAST_HORIZON_STEPS)]
    pv_history = repeat(pv_current, 4)
    wt_forecast = [wt_current * (1 + 0.02 * (i+1)) for i in range(FORECAST_HORIZON_STEPS)]
    wt_history = repeat(wt_current, 4)
    obs.extend([pv_current] + pv_forecast + pv_history)
    obs.extend([wt_current] + wt_forecast + wt_history)

    # Load demand (approx: base + EV/solar interaction proxy)
    base_load = 4000.0
    load_current = base_load + (wt_current * 0.01) - (pv_current * 0.05)
    load_forecast = [load_current * (1 + 0.01 * (i+1)) for i in range(FORECAST_HORIZON_STEPS)]
    load_history = repeat(load_current, 4)
    obs.extend([load_current] + load_forecast + load_history)

    # Battery status (per battery 6 features)
    if latest is None:
        soc = 0.5
        temperature = 30.0
    else:
        soc = float(latest.soc)/100.0 if latest.soc is not None else 0.5
        temperature = float(latest.temperature) if latest.temperature is not None else 30.0
    # Duplicate for second battery (placeholder). SoH=1, temp scaled /50, max rates=1, throughput≈0
    for i in range(BATTERY_COUNT):
        obs.extend([
            soc,          # soc
            1.0,          # soh
            temperature/50.0,
            1.0,          # max_charge ratio
            1.0,          # max_discharge ratio
            0.0           # cumulative throughput scaled
        ])

    # Grid price current + forecast + import/export limits (normalized)
    price_current = 0.12  # INR/kWh placeholder
    price_forecast = [price_current for _ in range(FORECAST_HORIZON_STEPS)]
    obs.append(price_current/100.0)
    obs.extend([p/100.0 for p in price_forecast])
    obs.extend([5000/10000.0, 3000/10000.0])  # import/export limits normalized

    # EV fleet status (5 features) - zero until EV tracking integrated
    obs.extend([0.0, 0.0, 0.0, 0.0, 0.0])

    # Component health indices (3): inverter temp, transformer load, voltage deviation
    obs.extend([
        temperature/50.0,  # inverter temp proxy
        0.5,               # transformer load factor placeholder
        0.0                # grid voltage deviation
    ])

    # Recent actions history (2 battery + grid + ev) * 4 = 16 values. (All zeros until we start tracking.)
    obs.extend([0.0]*16)

    return obs

def get_observation_dim() -> int:
    """Return expected observation length (static calc aligning with env_config)."""
    # Mirror env_config.OBS_SPACE.get_total_dim() components
    temporal = 4
    renew = (1 + FORECAST_HORIZON_STEPS + 4) * 2  # pv + wind blocks
    load = 1 + FORECAST_HORIZON_STEPS + 4
    battery_block = 6 * BATTERY_COUNT
    grid_block = 1 + FORECAST_HORIZON_STEPS + 2
    ev_block = 5
    health = 3
    recent = (BATTERY_COUNT * 4) + 4 + 4  # battery actions + grid + ev
    return temporal + renew + load + battery_block + grid_block + ev_block + health + recent
