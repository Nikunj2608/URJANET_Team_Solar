"""Simple safety supervisor (first stage).

Rules:
 - Enforce SoC envelope [20%, 90%]: block discharge below 20%, block charge above 90%.
 - Clamp aggregate battery power to rated limits.
 - Clamp grid import to max import; disallow export (set negative grid power to 0) for now.
 - Clamp EV charging and curtailment to feasible ranges.
Returns corrected semantic dict plus list of applied clamp flags.
"""
from __future__ import annotations
from typing import Dict, List, Tuple

BATTERY_MAX_CHARGE_TOTAL = 800.0  # 600 + 200 kW
BATTERY_MAX_DISCHARGE_TOTAL = 800.0
GRID_MAX_IMPORT = 5000.0
EV_MAX_CHARGE = 450.0

def apply_safety(semantic: Dict[str, float], soc_fraction: float) -> Tuple[Dict[str, float], List[str]]:
    safe = dict(semantic)
    flags: List[str] = []
    # SoC envelope logic
    if soc_fraction < 0.20 and safe['battery_kw'] < 0:
        safe['battery_kw'] = 0.0
        flags.append('BLOCK_DISCHARGE_LOW_SOC')
    if soc_fraction > 0.90 and safe['battery_kw'] > 0:
        safe['battery_kw'] = 0.0
        flags.append('BLOCK_CHARGE_HIGH_SOC')
    # Battery power clamp
    if safe['battery_kw'] > BATTERY_MAX_CHARGE_TOTAL:
        safe['battery_kw'] = BATTERY_MAX_CHARGE_TOTAL
        flags.append('CLAMP_BATTERY_CHARGE')
    if safe['battery_kw'] < -BATTERY_MAX_DISCHARGE_TOTAL:
        safe['battery_kw'] = -BATTERY_MAX_DISCHARGE_TOTAL
        flags.append('CLAMP_BATTERY_DISCHARGE')
    # Grid power (no export for now)
    if safe['grid_kw'] < 0:
        safe['grid_kw'] = 0.0
        flags.append('NO_EXPORT_SUPPORTED')
    if safe['grid_kw'] > GRID_MAX_IMPORT:
        safe['grid_kw'] = GRID_MAX_IMPORT
        flags.append('CLAMP_GRID_IMPORT')
    # EV
    if safe['ev_kw'] < 0:
        safe['ev_kw'] = 0.0
        flags.append('NEG_EV_POWER')
    if safe['ev_kw'] > EV_MAX_CHARGE:
        safe['ev_kw'] = EV_MAX_CHARGE
        flags.append('CLAMP_EV_CHARGE')
    # Curtailment
    if safe['curtailment'] < 0:
        safe['curtailment'] = 0.0
        flags.append('CURTAILMENT_NEG')
    if safe['curtailment'] > 1:
        safe['curtailment'] = 1.0
        flags.append('CURTAILMENT_GT1')
    return safe, flags
