from datetime import datetime, timezone
from typing import Any
import random

# Latest RL semantic adjustment (mutable module-level store)
_RL_SEMANTIC: dict[str, float] | None = None

def set_rl_semantic(semantic: dict[str, float] | None):
    global _RL_SEMANTIC
    _RL_SEMANTIC = semantic.copy() if semantic else None

def get_rl_semantic() -> dict[str, float] | None:
    return _RL_SEMANTIC.copy() if _RL_SEMANTIC else None

_BASE_TOPOLOGY = {
    "nodes": [
        {"id": "grid", "label": "Grid", "type": "grid", "x": 120, "y": 220, "metrics": {"power_kw": 18.5}},
        {"id": "solar", "label": "Solar", "type": "solar", "x": 120, "y": 60, "metrics": {"power_kw": 14.2}},
        {"id": "battery", "label": "Battery", "type": "battery", "x": 520, "y": 180, "metrics": {"soc": 62.4, "power_kw": -12.1}},
        {"id": "ev", "label": "EV Chargers", "type": "ev", "x": 840, "y": 100, "metrics": {"sessions": 3, "power_kw": 9.7}},
        {"id": "load", "label": "Facility Load", "type": "load", "x": 840, "y": 300, "metrics": {"power_kw": 32.9}},
    ],
    "edges": [
        {"from": "solar", "to": "battery", "power_kw": 8.1, "direction": "forward", "type": "charge"},
        {"from": "solar", "to": "load", "power_kw": 6.1, "direction": "forward", "type": "direct"},
        {"from": "grid", "to": "load", "power_kw": 18.5, "direction": "forward", "type": "import"},
        {"from": "battery", "to": "load", "power_kw": 4.0, "direction": "forward", "type": "discharge"},
        {"from": "battery", "to": "ev", "power_kw": 8.1, "direction": "forward", "type": "discharge"},
        {"from": "grid", "to": "ev", "power_kw": 1.6, "direction": "forward", "type": "import"},
    ]
}


def get_topology(dynamic: bool = False) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    if not dynamic:
        # Return copy
        import copy
        topo = copy.deepcopy(_BASE_TOPOLOGY)
        # Ensure direction field present (assume forward for initial static snapshot)
        for e in topo['edges']:
            if 'direction' not in e:
                e['direction'] = 'forward'
        topo["updated_at"] = now
        return topo
    # Dynamic: apply small bounded random perturbations to power flows & node metrics
    import copy
    topo = copy.deepcopy(_BASE_TOPOLOGY)
    import logging
    log = logging.getLogger(__name__)
    log.debug("dynamic_topology_start")
    try:
        for n in topo['nodes']:
            if 'power_kw' in n['metrics']:
                base = n['metrics']['power_kw']
                n['metrics']['power_kw'] = round(base + random.uniform(-1.2, 1.2), 2)
            if n['id'] == 'battery':
                base_soc = n['metrics']['soc']
                n['metrics']['soc'] = max(0.0, min(100.0, round(base_soc + random.uniform(-0.8, 0.8), 2)))
        for e in topo['edges']:
            base = e['power_kw']
            delta = random.uniform(-1.0, 1.0)
            new_val = base + delta
            if e['type'] in ('discharge','charge') and random.random() < 0.15:
                new_val = -abs(new_val)
            e['power_kw'] = round(new_val, 2)
            e['direction'] = 'forward' if e['power_kw'] >= 0 else 'reverse'
        # Apply RL semantic override if present
        if _RL_SEMANTIC:
            b = _RL_SEMANTIC.get('battery_kw')
            g = _RL_SEMANTIC.get('grid_kw')
            ev = _RL_SEMANTIC.get('ev_kw')
            # Battery discharge edges
            for e in topo['edges']:
                if e['from']=='battery' and e['to'] in ('load','ev'):
                    if b is not None:
                        if b < 0:  # discharge
                            e['power_kw'] = round(min(abs(b)/100.0, 40),2)
                            e['direction'] = 'forward'
                        elif b > 0:  # charging -> minimal reverse hint
                            e['power_kw'] = round(min(b/200.0, 5),2)
                            e['direction'] = 'reverse'
                if e['from']=='solar' and e['to']=='battery' and b is not None and b>0:
                    e['power_kw'] = round(min(b/80.0, 30),2)
                    e['direction'] = 'forward'
                if e['from']=='grid' and e['to']=='load' and g is not None:
                    if g > 0: # import
                        e['power_kw'] = round(min(g/80.0, 50),2)
                        e['direction'] = 'forward'
                    elif g < 0: # export
                        e['power_kw'] = round(min(abs(g)/80.0, 50),2)
                        e['direction'] = 'reverse'
                if e['from']=='grid' and e['to']=='ev' and ev is not None and ev>0:
                    e['power_kw'] = round(min(ev/20.0, 30),2)
                    e['direction'] = 'forward'
        for e in topo['edges']:
            if 'direction' not in e:
                e['direction'] = 'forward'
            log.debug("edge %s->%s %s %.2f", e['from'], e['to'], e['direction'], e['power_kw'])
        log.debug("dynamic_topology_complete")
    except Exception as e:  # pragma: no cover
        log.debug("dynamic_topology_error %s", e)
    topo['updated_at'] = now
    return topo


def get_static_topology() -> dict[str, Any]:  # retained for backward compatibility
    return get_topology(dynamic=False)
