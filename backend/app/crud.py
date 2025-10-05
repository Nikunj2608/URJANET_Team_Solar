from sqlalchemy.orm import Session
from . import models
from .schemas import TelemetryIn
from datetime import datetime


def ensure_device(db: Session, device_id: str):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        device = models.Device(id=device_id, name=f"Device {device_id[:8]}")
        db.add(device)
        db.commit()
        db.refresh(device)
    return device


def insert_telemetry(db: Session, data: TelemetryIn):
    ensure_device(db, data.device_id)
    row = models.Telemetry(device_id=data.device_id, voltage=data.voltage, soc=data.soc, temperature=data.temperature)
    db.add(row)
    db.commit()
    # no autoincrement id; merged state already populated
    return row


def list_devices(db: Session):
    return db.query(models.Device).order_by(models.Device.created_at).all()


def latest_telemetry(db: Session, device_id: str):
    return (db.query(models.Telemetry)
              .filter(models.Telemetry.device_id == device_id)
              .order_by(models.Telemetry.ts.desc())
              .first())


def telemetry_range(db: Session, device_id: str, start, end, limit: int = 1000):
    q = (db.query(models.Telemetry)
           .filter(models.Telemetry.device_id == device_id)
           .filter(models.Telemetry.ts >= start)
           .filter(models.Telemetry.ts <= end)
           .order_by(models.Telemetry.ts.asc())
           .limit(limit))
    return q.all()


def list_alerts(db: Session, device_id: str | None = None, limit: int = 50):
    q = db.query(models.Alert).order_by(models.Alert.ts.desc())
    if device_id:
        q = q.filter(models.Alert.device_id == device_id)
    return q.limit(limit).all()


def create_alert(db: Session, *, device_id: str, type_: str, severity: str, message: str, value: float, threshold: float):
    alert = models.Alert(device_id=device_id, type=type_, severity=severity, message=message, value=value, threshold=threshold)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def acknowledge_alert(db: Session, alert_id: int):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        return None
    if alert.ack_ts is None:
        alert.ack_ts = datetime.utcnow()
        db.add(alert)
        db.commit()
        db.refresh(alert)
    return alert


def risk_alert_exists(db: Session, device_id: str, type_: str):
    return db.query(models.Alert).filter(models.Alert.device_id==device_id, models.Alert.type==type_).order_by(models.Alert.ts.desc()).first()


def log_rl_decision(db: Session, *, device_id: str, obs: list[float], raw_vector: list[float] | None,
                    semantic_raw: dict | None, semantic_safe: dict | None, safety_flags: list[str] | None,
                    value_estimate: float | None):
    entry = models.RLDecisionLog(
        device_id=device_id,
        obs=obs,
        raw_vector=raw_vector,
        semantic_raw=semantic_raw,
        semantic_safe=semantic_safe,
        safety_flags=safety_flags,
        value_estimate=value_estimate
    )
    db.add(entry)
    db.commit()
    return entry


def list_rl_decisions(db: Session, device_id: str, limit: int = 25, before_id: int | None = None):
    q = (db.query(models.RLDecisionLog)
        .filter(models.RLDecisionLog.device_id == device_id))
    if before_id is not None:
        q = q.filter(models.RLDecisionLog.id < before_id)
    q = q.order_by(models.RLDecisionLog.id.desc()).limit(limit + 1)  # grab one extra for has_more
    rows = q.all()
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    return rows, has_more


def recent_telemetry(db: Session, device_id: str, limit: int = 10):
    """Return most recent telemetry rows (descending ts)."""
    return (db.query(models.Telemetry)
              .filter(models.Telemetry.device_id == device_id)
              .order_by(models.Telemetry.ts.desc())
              .limit(limit)
              .all())


# --- Chat history persistence ---
def add_chat_message(db: Session, *, device_id: str, role: str, content: str, model: str | None = None, meta: dict | None = None):
    msg = models.ChatMessage(device_id=device_id, role=role, content=content, model=model, meta=meta)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_chat_messages(db: Session, device_id: str, limit: int = 20):
    return (db.query(models.ChatMessage)
              .filter(models.ChatMessage.device_id == device_id)
              .order_by(models.ChatMessage.id.desc())
              .limit(limit)
              .all())

