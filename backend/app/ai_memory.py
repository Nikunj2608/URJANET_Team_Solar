"""Simple in-memory chat history storage (non-persistent).
Not for production use (no eviction beyond max_per_device).
"""
from __future__ import annotations
from collections import deque
from typing import Deque, Tuple, Dict

_MAX_PER_DEVICE = 8  # keep last 8 exchanges (Q,A)
_history: Dict[str, Deque[Tuple[str,str]]] = {}

def add_exchange(device_id: str, question: str, answer: str):
    dq = _history.setdefault(device_id, deque(maxlen=_MAX_PER_DEVICE))
    dq.append((question, answer))

def get_history(device_id: str) -> list[dict]:
    dq = _history.get(device_id)
    if not dq:
        return []
    return [ {"q": q, "a": a} for (q,a) in list(dq) ]
