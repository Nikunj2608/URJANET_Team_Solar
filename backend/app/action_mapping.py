"""Continuous action vector → semantic power flow mapping.

The trained PPO outputs a mean action vector in [-1,1] per dimension in the
ordering:
  [ battery_1, battery_2, grid_power, ev_charging, renewable_curtailment ]

We map / denormalize these to engineering units using the same conventions as
the training environment (see microgrid_env._parse_actions) and then produce a
compact semantic dict suitable for UX display & safety supervision.
"""
from __future__ import annotations
from typing import Dict, List

# Mirrors env_config capacities (duplicated lightweight values to avoid heavy import)
BAT1_MAX_CHARGE = 600.0
BAT1_MAX_DISCHARGE = 600.0
BAT2_MAX_CHARGE = 200.0
BAT2_MAX_DISCHARGE = 200.0
GRID_MAX_IMPORT = 5000.0
GRID_MAX_EXPORT = 3000.0
EV_MAX_AGG_CHARGE = 450.0   # Approx sum of chargers (placeholder)

def get_capacities() -> dict:
    """Expose capacity constants for frontend scaling without duplication.

    Returns a dict of max charge/discharge/import/export and EV aggregate limits.
    """
    return {
        'BAT1_MAX_CHARGE': BAT1_MAX_CHARGE,
        'BAT1_MAX_DISCHARGE': BAT1_MAX_DISCHARGE,
        'BAT2_MAX_CHARGE': BAT2_MAX_CHARGE,
        'BAT2_MAX_DISCHARGE': BAT2_MAX_DISCHARGE,
        'GRID_MAX_IMPORT': GRID_MAX_IMPORT,
        'GRID_MAX_EXPORT': GRID_MAX_EXPORT,
        'EV_MAX_AGG_CHARGE': EV_MAX_AGG_CHARGE
    }

def _battery_power_component(raw: float, max_charge: float, max_discharge: float) -> float:
    if raw >= 0:
        return raw * max_charge  # positive = charging
    return raw * max_discharge   # negative value

def map_action(raw_vector: List[float]) -> Dict[str, float]:
    if not raw_vector:
        return {
            'battery_kw': 0.0,
            'battery1_kw': 0.0,
            'battery2_kw': 0.0,
            'grid_kw': 0.0,
            'ev_kw': 0.0,
            'curtailment': 0.0
        }
    v = raw_vector
    # Defensive: pad if shorter
    while len(v) < 5:
        v.append(0.0)
    b1 = _battery_power_component(v[0], BAT1_MAX_CHARGE, BAT1_MAX_DISCHARGE)
    b2 = _battery_power_component(v[1], BAT2_MAX_CHARGE, BAT2_MAX_DISCHARGE)
    grid_norm = v[2]
    if grid_norm >= 0:
        grid_kw = grid_norm * GRID_MAX_IMPORT
    else:
        grid_kw = -grid_norm * GRID_MAX_EXPORT * -1  # export represented negative
    ev_norm = max(0.0, min(1.0, v[3]))
    ev_kw = ev_norm * EV_MAX_AGG_CHARGE
    curtailment = (v[4] + 1) / 2.0  # [-1,1] → [0,1]
    total_battery = b1 + b2  # positive charging, negative discharging
    return {
        'battery_kw': total_battery,
        'battery1_kw': b1,
        'battery2_kw': b2,
        'grid_kw': grid_kw,
        'ev_kw': ev_kw,
        'curtailment': max(0.0, min(1.0, curtailment))
    }
