import logging
import os
import asyncio
from typing import List, Any

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import init_db, get_db
from . import crud, schemas, rules
from .rl_obs import build_observation
from .action_mapping import map_action, get_capacities
from .safety import apply_safety
from .mqtt import MQTTIngestor
from . import flow as flow_module
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, push_to_gateway
from .emailer import EmailAlertSender
from . import ai_gemini
from . import ai_memory

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
email_sender = EmailAlertSender()

app = FastAPI(title="Next-Gen EMS Prototype", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# --- Simple WebSocket connection registry ---
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        living = []
        for ws in self.active:
            try:
                await ws.send_json(message)
                living.append(ws)
            except Exception:
                pass
        self.active = living


manager = ConnectionManager()


INGEST_OK = Counter('telemetry_ingest_ok_total', 'Successful telemetry ingestions')
INGEST_FAIL = Counter('telemetry_ingest_fail_total', 'Failed telemetry ingestions')
ALERT_CREATED = Counter('alerts_created_total', 'Alerts created by rules', ['type','severity'])
_bucket_env = os.getenv('PROMETHEUS_LATENCY_BUCKETS')  # comma-separated floats
if _bucket_env:
    try:
        _buckets = tuple(float(x) for x in _bucket_env.split(',') if x.strip())
    except Exception:
        _buckets = Histogram.DEFAULT_BUCKETS
else:
    _buckets = Histogram.DEFAULT_BUCKETS
INGEST_LATENCY = Histogram('telemetry_persist_seconds', 'DB persist duration seconds', buckets=_buckets)
LAST_TS_GAUGE = Gauge('telemetry_last_timestamp', 'Unix timestamp of last telemetry per device', ['device_id'])
DEDUP_DISCARDED = Counter('telemetry_dedup_discarded_total', 'Telemetry messages discarded due to duplicate (device_id, ts)')
RL_DECISIONS_TOTAL = Counter('rl_decision_total', 'Total RL decisions processed', ['device_id'])
RL_DECISIONS_FLAGGED_TOTAL = Counter('rl_decision_flagged_total', 'RL decisions with one or more safety flags', ['device_id'])
AI_CHAT_REQUESTS = Counter('ai_chat_requests_total', 'AI chat requests received', ['device_id','fallback'])
AI_INSIGHT_GENERATED = Counter('ai_insight_generated_total', 'AI insight generations', ['device_id','cached','fallback'])
AI_LATENCY = Histogram('ai_inference_seconds', 'AI call latency seconds', ['endpoint','model'])

# Simple in-memory dedup cache (LRU-like with max size)
_dedup_cache: dict[tuple[str,str], None] = {}
_DEDUP_MAX = 5000

def _dedup_key(device_id: str, ts_iso: str) -> tuple[str,str]:
    return (device_id, ts_iso)

def handle_ingested(payload: dict):
    """Handle telemetry from MQTT thread: persist, enqueue events for async dispatch."""
    from .schemas import TelemetryIn
    from .database import SessionLocal
    loop: asyncio.AbstractEventLoop | None = getattr(app.state, 'loop', None)
    event_queue: asyncio.Queue | None = getattr(app.state, 'event_queue', None)
    db = SessionLocal()
    try:
        telem = TelemetryIn(**payload)
        # Assign ts if absent (for dedup key); DB adds default but we want deterministic key
        if 'ts' in payload:
            ts_iso = str(payload['ts'])
        else:
            from datetime import datetime, timezone
            ts_iso = datetime.now(timezone.utc).isoformat()
            payload['ts'] = ts_iso
        key = _dedup_key(telem.device_id, ts_iso)
        if key in _dedup_cache:
            DEDUP_DISCARDED.inc()
            return
        # Trim cache if over size
        if len(_dedup_cache) >= _DEDUP_MAX:
            # Drop arbitrary 10% oldest (iteration order insertion-based in CPython 3.7+)
            for i, k in enumerate(list(_dedup_cache.keys())):
                del _dedup_cache[k]
                if i > _DEDUP_MAX//10:
                    break
        _dedup_cache[key] = None
        import time
        start_t = time.perf_counter()
        row = crud.insert_telemetry(db, telem)
        INGEST_OK.inc()
        INGEST_LATENCY.observe(time.perf_counter()-start_t)
        LAST_TS_GAUGE.labels(device_id=telem.device_id).set(row.ts.timestamp())
        logger.info("Ingested telemetry device=%s v=%.2f soc=%.2f temp=%.2f", telem.device_id, telem.voltage, telem.soc, telem.temperature)
        telemetry_event = {"type": "telemetry", "data": schemas.TelemetryOut.model_validate(row).model_dump()}
        alert_events: list[dict[str, Any]] = []
        for alert_payload in rules.evaluate(payload):
            alert = crud.create_alert(db, device_id=telem.device_id, **alert_payload)
            ALERT_CREATED.labels(type=alert_payload['type_'], severity=alert_payload['severity']).inc()
            alert_out = schemas.AlertOut.model_validate(alert).model_dump()
            alert_events.append({"type": "alert", "data": alert_out})
            # Fire-and-forget email (cooldown per alert type severity)
            if email_sender.enabled:
                key = f"{alert_payload['type_']}:{alert_payload['severity']}"
                subj = f"EMS Alert: {alert_payload['type_']} ({alert_payload['severity']})"
                body = (
                    f"Device: {telem.device_id}\n"
                    f"Type: {alert_payload['type_']}\n"
                    f"Severity: {alert_payload['severity']}\n"
                    f"Message: {alert_payload.get('message','')}\n"
                    f"Value: {alert_payload.get('value')} Threshold: {alert_payload.get('threshold')}\n"
                )
                sent = email_sender.send(subj, body, key=key)
                if sent:
                    logger.info("Alert email dispatched key=%s", key)
        if loop and event_queue and not loop.is_closed():
            # Enqueue without awaiting (thread-safe)
            loop.call_soon_threadsafe(event_queue.put_nowait, telemetry_event)
            for ev in alert_events:
                loop.call_soon_threadsafe(event_queue.put_nowait, ev)
    except Exception as e:
        INGEST_FAIL.inc()
        logger.warning("Failed to handle telemetry: %s", e)
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    # Store event loop & create event queue + dispatcher
    loop = asyncio.get_event_loop()
    app.state.loop = loop
    app.state.event_queue = asyncio.Queue()

    async def dispatcher():
        q: asyncio.Queue = app.state.event_queue
        while True:
            event = await q.get()
            try:
                await manager.broadcast(event)
            except Exception as e:  # pragma: no cover
                logger.debug("Broadcast failed: %s", e)
            finally:
                q.task_done()

    app.state.dispatcher_task = loop.create_task(dispatcher())
    init_db()
    ingestor = MQTTIngestor(on_telemetry=handle_ingested)
    ingestor.start()
    app.state.ingestor = ingestor
    # Launch risk-aware alert loop
    async def risk_loop():
        from datetime import datetime
        import httpx
        device_id = os.getenv('PRIMARY_DEVICE_ID','11111111-1111-1111-1111-111111111111')
        while True:
            try:
                url = f"http://localhost:{os.getenv('BACKEND_PORT','18000')}/forecast/battery?device_id={device_id}"
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        js = resp.json()
                        risk = js.get('risk_score')
                        if risk and risk > 0.75:
                            db = next(get_db())
                            existing = crud.risk_alert_exists(db, device_id, 'BATTERY_SOC_RISK')
                            fresh = True
                            if existing:
                                age = (datetime.utcnow() - existing.ts).total_seconds()
                                if age < 600:
                                    fresh = False
                            if fresh:
                                crud.create_alert(db, device_id=device_id, type_='BATTERY_SOC_RISK', severity='MEDIUM', message='Projected Risk: Battery SoC may fall below critical 15% threshold in horizon.', value=0.0, threshold=15.0)
                            db.close()
            except Exception:
                pass
            await asyncio.sleep(30)
    app.state.risk_task = loop.create_task(risk_loop())
    logger.info("Startup complete")
    # Optional pushgateway
    pgw = os.getenv('PROMETHEUS_PUSHGATEWAY')
    if pgw:
        import threading, time
        def _push_loop():
            while True:
                try:
                    push_to_gateway(pgw, job='ems_backend', registry=CollectorRegistry())  # push default
                except Exception as e:  # pragma: no cover
                    logger.debug("Pushgateway push failed: %s", e)
                time.sleep(int(os.getenv('PROMETHEUS_PUSH_INTERVAL','30')))
        threading.Thread(target=_push_loop, daemon=True).start()


@app.on_event("shutdown")
async def shutdown():
    task = getattr(app.state, 'dispatcher_task', None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass
    ingestor = getattr(app.state, 'ingestor', None)
    if ingestor:
        try:
            ingestor.stop()
        except Exception:
            pass
    risk_task = getattr(app.state, 'risk_task', None)
    if risk_task:
        risk_task.cancel()
        try:
            await risk_task
        except Exception:
            pass


@app.get("/health", response_model=schemas.HealthStatus)
def health():
    return {"status": "ok"}


@app.get("/devices", response_model=List[schemas.DeviceOut])
def get_devices(db: Session = Depends(get_db)):
    return crud.list_devices(db)


@app.post("/telemetry", response_model=schemas.TelemetryOut)
def post_telemetry(payload: schemas.TelemetryIn, db: Session = Depends(get_db)):
    row = crud.insert_telemetry(db, payload)
    # Evaluate rules & possibly create alerts
    for alert_payload in rules.evaluate(payload.model_dump()):
        # Backward compatibility: rules now yield 'type_' but sanitize just in case
        if 'type' in alert_payload and 'type_' not in alert_payload:
            alert_payload['type_'] = alert_payload.pop('type')
        crud.create_alert(db, device_id=payload.device_id, **alert_payload)
    return row


@app.get("/telemetry/latest", response_model=schemas.TelemetryOut | None)
def latest(device_id: str = Query(...), db: Session = Depends(get_db)):
    return crud.latest_telemetry(db, device_id)


@app.get("/telemetry/range", response_model=list[schemas.TelemetryOut])
def telemetry_range(
    device_id: str = Query(...),
    start: str = Query(..., description="ISO8601 start timestamp"),
    end: str = Query(..., description="ISO8601 end timestamp"),
    limit: int = Query(1000, le=10000, description="Max rows"),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid datetime format; use ISO8601")
    rows = crud.telemetry_range(db, device_id, start_dt, end_dt, limit=limit)
    return rows


@app.get("/mqtt/stats")
def mqtt_stats():
    ingestor = getattr(app.state, 'ingestor', None)
    if not ingestor:
        return {"status": "not-running"}
    return {"status": "ok", **ingestor.stats()}

@app.get("/flow/topology")
def flow_topology():
    return flow_module.get_static_topology()

@app.get("/flow/topology/delta")
def flow_topology_delta():
    # Provide slightly perturbed values to animate change client side
    try:
        logger.debug("/flow/topology/delta request start")
        topo = flow_module.get_topology(dynamic=True)
        logger.debug("/flow/topology/delta ok edges=%d nodes=%d", len(topo.get('edges', [])), len(topo.get('nodes', [])))
        return topo
    except Exception as e:  # pragma: no cover
        logger.exception("/flow/topology/delta failure: %s", e)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="delta_generation_failed")


@app.get('/metrics')
def metrics_endpoint(auth: str | None = Query(default=None, description="Basic auth token if METRICS_BASIC_AUTH configured")):
    # Basic auth via static token (simple demo). Set METRICS_BASIC_AUTH="user:pass" and request with ?auth=base64(user:pass)
    configured = os.getenv('METRICS_BASIC_AUTH')
    if configured:
        import base64
        if not auth or auth != base64.b64encode(configured.encode()).decode():
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail='Unauthorized metrics')
    data = generate_latest()
    from fastapi import Response
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/alerts", response_model=List[schemas.AlertOut])
def get_alerts(device_id: str | None = None, db: Session = Depends(get_db)):
    return crud.list_alerts(db, device_id=device_id)


@app.get("/alerts/smart", response_model=List[schemas.SmartAlertOut])
def get_smart_alerts(device_id: str | None = None, db: Session = Depends(get_db)):
    # Basic enrichment: map severity/type to a mock recommended action
    base = crud.list_alerts(db, device_id=device_id)
    recommendations = {
        'SOC_LOW': 'Schedule opportunistic charge within next hour to avoid deep discharge.',
        'VOLTAGE_HIGH': 'Investigate inverter settings / reduce high demand circuits.',
        'TEMP_HIGH': 'Reduce charge/discharge rate; check cooling airflow.',
        'BATTERY_SOC_RISK': 'Consider shedding non-essential loads or pre-charging from grid if tariff favourable.'
    }
    out: list[schemas.SmartAlertOut] = []
    for a in base:
        rec = recommendations.get(a.type, None)
        d = schemas.SmartAlertOut.model_validate(a).model_dump()
        d['recommended_action'] = rec
        d['risk_generated'] = (a.type == 'BATTERY_SOC_RISK')
        out.append(schemas.SmartAlertOut(**d))
    return out


@app.post('/alerts/{alert_id}/ack', response_model=schemas.AckResponse)
def acknowledge(alert_id: int, db: Session = Depends(get_db)):
    a = crud.acknowledge_alert(db, alert_id)
    if not a:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Alert not found')
    return schemas.AckResponse(id=a.id, ack_ts=a.ack_ts)


@app.post('/debug/trigger-risk-alert', response_model=schemas.AlertOut)
def trigger_risk_alert(device_id: str = Query('11111111-1111-1111-1111-111111111111'), db: Session = Depends(get_db)):
    # Force insert a BATTERY_SOC_RISK alert (demo tool)
    alert = crud.create_alert(
        db,
        device_id=device_id,
        type_='BATTERY_SOC_RISK',
        severity='MEDIUM',
        message='(Demo) Forced Risk: Battery SoC may fall below critical threshold.',
        value=0.0,
        threshold=15.0,
    )
    # Send email for manual demo alert as well
    if email_sender.enabled:
        key = f"{alert.type}:{alert.severity}"
        subj = f"EMS Alert (Manual Trigger): {alert.type} ({alert.severity})"
        body = (
            f"Device: {alert.device_id}\n"
            f"Type: {alert.type}\n"
            f"Severity: {alert.severity}\n"
            f"Message: {alert.message}\n"
            f"Value: {alert.value} Threshold: {alert.threshold}\n"
        )
        if email_sender.send(subj, body, key=key):
            logger.info("Manual alert email dispatched key=%s", key)
    return alert


@app.post('/debug/test-email')
def test_email(subject: str = Query('Test EMS Email'), body: str = Query('This is a test alert email.'), key: str = Query('TEST:INFO')):
        """Send a test email via the configured SMTP settings.

        Query params:
            subject: custom subject
            body: body content
            key: cooldown key (change to bypass cooldown)
        Returns JSON with 'sent': bool and 'enabled': bool.
        """
        if not email_sender.enabled:
                return {"enabled": False, "sent": False, "reason": "Email sender not enabled (check SMTP_HOST and ALERT_EMAIL_RECIPIENTS)"}
        sent = email_sender.send(subject, body, key=key)
        return {"enabled": True, "sent": sent, "cooldown_key": key}


@app.get('/advisory/rl', response_model=schemas.RLAdvisoryOut)
def rl_advisory(device_id: str = Query(...)):
    """Fetch latest RL advisory.

    If RL agent microservice configured (RL_AGENT_URL), query it live; else fall back to static mock.
    """
    from datetime import datetime, timezone
    import httpx
    now = datetime.now(timezone.utc)
    rl_url = os.getenv('RL_AGENT_URL', 'http://rl-agent:8001/get-action')
    # Gather minimal state
    from .database import SessionLocal
    db = SessionLocal()
    latest = crud.latest_telemetry(db, device_id)
    db.close()
    if latest is None:
        soc = 50.0
        voltage = 230.0
        temp = 30.0
    else:
        soc = float(latest.soc)
        voltage = float(latest.voltage)
        temp = float(latest.temperature)
    # Build full observation (placeholder enriched) and still include legacy scalar fields for backward compatible RL service
    obs = build_observation(device_id)
    payload = {
        'battery_soc': soc,
        'solar_output_kw': 8.0,
        'grid_price_per_kwh': 0.12,
        'current_load_kw': round(voltage * 0.02, 2),
        'observation': obs  # new optional full vector
    }
    actions: list[schemas.RLActionOut]
    try:
        with httpx.Client(timeout=2.5) as client:
            resp = client.post(rl_url, json=payload)
        if resp.status_code == 200:
            rj = resp.json()
            base_action = rj.get('action', 'HOLD')
            conf = float(rj.get('confidence', 0.0))
            rationale = rj.get('rationale', '')
            model_version = rj.get('model_version')
            raw_vec = rj.get('raw_vector') or []
            value_est = rj.get('value_estimate') if 'value_estimate' in rj else None
            impact_map = {
                'CHARGE_BATTERY': 3.0,
                'DISCHARGE_BATTERY_TO_LOAD': -4.0,
                'HOLD': 0.0
            }
            impact = impact_map.get(base_action, 0.0)
            actions = [schemas.RLActionOut(
                id=base_action.lower(),
                title=base_action.replace('_',' ').title(),
                description=rationale,
                impact_kw=impact,
                confidence=conf,
                horizon_min=30,
                raw_vector=raw_vec,
                value_estimate=value_est
            )]
            return schemas.RLAdvisoryOut(generated_at=now, device_id=device_id, actions=actions, model_version=model_version)
    except Exception as e:  # pragma: no cover
        logger.debug("RL advisory fetch failed: %s", e)
    # Fallback mock
    actions = [
        schemas.RLActionOut(
            id='fallback_charge_shift',
            title='Shift Charge Window',
            description='(Fallback) Delay bulk battery charge until solar ramp to reduce grid import.',
            impact_kw=-3.0,
            confidence=0.5,
            horizon_min=30
        )
    ]
    return schemas.RLAdvisoryOut(generated_at=now, device_id=device_id, actions=actions, model_version='fallback')


@app.get('/advisory/rl/safe', response_model=schemas.RLSafeAdvisoryOut)
def rl_advisory_safe(device_id: str = Query(...)):
    """Fetch RL advisory + semantic action mapping + safety supervision.

    This endpoint builds the full observation vector, queries the RL service,
    derives semantic engineering units, applies safety clamps, logs the
    decision, and returns both raw & safe semantics for transparency.
    """
    from datetime import datetime, timezone
    import httpx
    now = datetime.now(timezone.utc)
    # Gather latest SoC for safety logic
    from .database import SessionLocal
    db = SessionLocal()
    latest = crud.latest_telemetry(db, device_id)
    soc_pct = float(latest.soc) if latest and latest.soc is not None else 50.0
    # Observation
    obs = build_observation(device_id)
    rl_url = os.getenv('RL_AGENT_URL', 'http://rl-agent:8001/get-action')
    payload = {
        'battery_soc': soc_pct,
        'solar_output_kw': 8.0,
        'grid_price_per_kwh': 0.12,
        'current_load_kw': (float(latest.voltage) if latest and latest.voltage else 230.0) * 0.02,
        'observation': obs
    }
    try:
        import httpx
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(rl_url, json=payload)
        if resp.status_code == 200:
            rj = resp.json()
            raw_vec = rj.get('raw_vector') or []
            semantic_raw = map_action(list(raw_vec)) if raw_vec else None
            soc_fraction = soc_pct / 100.0
            semantic_safe, flags = apply_safety(semantic_raw, soc_fraction) if semantic_raw else (None, [])
            base_action = rj.get('action','HOLD')
            conf = float(rj.get('confidence',0.0))
            value_est = rj.get('value_estimate')
            rationale = rj.get('rationale','')
            model_version = rj.get('model_version')
            impact_map = {
                'CHARGE_BATTERY': 3.0,
                'DISCHARGE_BATTERY_TO_LOAD': -4.0,
                'HOLD': 0.0
            }
            impact = impact_map.get(base_action,0.0)
            action = schemas.RLActionOut(
                id=base_action.lower(),
                title=base_action.replace('_',' ').title(),
                description=rationale,
                impact_kw=impact,
                confidence=conf,
                horizon_min=30,
                raw_vector=raw_vec,
                value_estimate=value_est,
                semantic_raw=semantic_raw,
                semantic_safe=semantic_safe,
                safety_flags=flags or None
            )
            # Persist RL semantic for flow visualization (prefer safe if available)
            try:
                from . import flow as flow_module
                flow_module.set_rl_semantic(semantic_safe or semantic_raw)
            except Exception:
                pass
            # Log decision
            crud.log_rl_decision(db, device_id=device_id, obs=obs, raw_vector=raw_vec,
                                 semantic_raw=semantic_raw, semantic_safe=semantic_safe,
                                 safety_flags=flags, value_estimate=value_est)
            # Metrics counters
            try:
                RL_DECISIONS_TOTAL.labels(device_id=device_id).inc()
                if flags:
                    RL_DECISIONS_FLAGGED_TOTAL.labels(device_id=device_id).inc()
            except Exception:  # pragma: no cover
                pass
            db.close()
            return schemas.RLSafeAdvisoryOut(generated_at=now, device_id=device_id, actions=[action], model_version=model_version)
    except Exception as e:  # pragma: no cover
        try: db.close()
        except Exception: pass
        logger.debug("Safe RL advisory failed: %s", e)
    # Fallback with observation logged
    fallback_action = schemas.RLActionOut(
        id='fallback_hold',
        title='Hold (Fallback)',
        description='(Fallback) RL agent unavailable. Holding current operating point.',
        impact_kw=0.0,
        confidence=0.0,
        horizon_min=30
    )
    return schemas.RLSafeAdvisoryOut(generated_at=now, device_id=device_id, actions=[fallback_action], model_version='fallback')


@app.get('/advisory/rl/history', response_model=schemas.RLDecisionHistoryOut)
def rl_history(
    device_id: str = Query(...),
    limit: int = Query(25, le=200),
    before_id: int | None = Query(None, description="Return entries with id < before_id (cursor)")
):
    """Return recent RL decisions with semantic safe/raw, deltas & safety flags.

    Pagination: supply before_id from previous response's next_before_id.
    """
    from .database import SessionLocal
    db = SessionLocal()
    rows, has_more = crud.list_rl_decisions(db, device_id=device_id, limit=limit, before_id=before_id)
    items: list[schemas.RLDecisionHistoryItem] = []
    min_id = None
    for r in rows:
        if min_id is None or r.id < min_id:
            min_id = r.id
        ve = float(r.value_estimate) if r.value_estimate is not None else None
        # Compute semantic delta raw-safe if both exist and numeric
        semantic_delta = None
        if r.semantic_raw and r.semantic_safe:
            semantic_delta = {}
            for k, v in r.semantic_raw.items():
                try:
                    raw_v = float(v)
                    safe_v = float(r.semantic_safe.get(k)) if k in r.semantic_safe else None
                    if safe_v is not None:
                        semantic_delta[k] = raw_v - safe_v
                except Exception:
                    pass
        items.append(schemas.RLDecisionHistoryItem(
            id=r.id,
            ts=r.ts,
            value_estimate=ve,
            safety_flags=r.safety_flags,
            semantic_safe=r.semantic_safe,
            semantic_raw=r.semantic_raw,
            semantic_delta=semantic_delta
        ))
    db.close()
    next_before = min_id if has_more and min_id is not None else None
    return schemas.RLDecisionHistoryOut(device_id=device_id, decisions=items, next_before_id=next_before, has_more=has_more)


@app.get('/advisory/rl/history/export')
def rl_history_export(
    device_id: str = Query(...),
    limit: int = Query(500, le=5000),
    before_id: int | None = Query(None)
):
    """Export RL decision history as CSV (descending id order until limit)."""
    import csv, io
    from .database import SessionLocal
    db = SessionLocal()
    rows, _ = crud.list_rl_decisions(db, device_id=device_id, limit=limit, before_id=before_id)
    db.close()
    output = io.StringIO()
    fieldnames = [
        'id','ts','device_id','value_estimate','safety_flags','raw_vector'
    ]
    # Extend with semantic raw/safe keys union for consistent columns
    semantic_keys = set()
    for r in rows:
        if isinstance(r.semantic_raw, dict):
            semantic_keys.update(r.semantic_raw.keys())
        if isinstance(r.semantic_safe, dict):
            semantic_keys.update(r.semantic_safe.keys())
    semantic_keys = sorted(list(semantic_keys))
    for k in semantic_keys:
        fieldnames.append(f'sem_raw_{k}')
    for k in semantic_keys:
        fieldnames.append(f'sem_safe_{k}')
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        row = {
            'id': r.id,
            'ts': r.ts.isoformat(),
            'device_id': r.device_id,
            'value_estimate': float(r.value_estimate) if r.value_estimate is not None else '',
            'safety_flags': '|'.join(r.safety_flags) if r.safety_flags else '',
            'raw_vector': ';'.join(str(x) for x in (r.raw_vector or [])),
        }
        for k in semantic_keys:
            row[f'sem_raw_{k}'] = r.semantic_raw.get(k) if r.semantic_raw else ''
            row[f'sem_safe_{k}'] = r.semantic_safe.get(k) if r.semantic_safe else ''
        writer.writerow(row)
    from fastapi import Response
    csv_bytes = output.getvalue().encode()
    return Response(content=csv_bytes, media_type='text/csv', headers={
        'Content-Disposition': f'attachment; filename="rl_history_{device_id}.csv"'
    })


@app.post('/api/evaluate-action', response_model=schemas.ActionCostResponse)
def evaluate_action(req: schemas.ActionCostRequest):
    """Estimate cost (INR) over a short horizon for a proposed action.

    Simplified heuristic model:
    - Compute net battery power change based on action label.
    - Limit by available SoC (for discharge) and headroom (for charge).
    - Assume constant load and solar over horizon.
    - Cost = (grid_import_kwh * grid_price_per_kwh * 1000)  (convert kWh * price to INR).
    - Negative cost (savings) allowed if exporting (not modeled here -> zeroed).
    """
    horizon_hours = max(1, req.horizon_min) / 60.0
    soc = max(0.0, min(100.0, req.battery_soc))
    capacity_kwh = 100.0  # assumed nominal battery capacity for prototype
    usable_kwh = capacity_kwh * (soc / 100.0)
    headroom_kwh = capacity_kwh - usable_kwh
    base_load_kw = req.current_load_kw
    solar_kw = req.solar_output_kw
    # Action translation (very coarse for demo)
    if req.action == 'DISCHARGE_BATTERY_TO_LOAD':
        target_discharge_kw = min( (usable_kwh / horizon_hours) * 0.6, base_load_kw * 0.8 )
        discharge_kw = max(0.0, target_discharge_kw)
        battery_delta_kwh = discharge_kw * horizon_hours
        grid_import_kw = max(0.0, base_load_kw - solar_kw - discharge_kw)
    elif req.action == 'CHARGE_BATTERY':
        target_charge_kw = min( (headroom_kwh / horizon_hours) * 0.6, solar_kw * 0.9 )
        charge_kw = max(0.0, target_charge_kw)
        battery_delta_kwh = -charge_kw * horizon_hours  # negative (charging)
        grid_import_kw = max(0.0, base_load_kw - solar_kw + charge_kw)
    else:  # HOLD or unknown
        battery_delta_kwh = 0.0
        grid_import_kw = max(0.0, base_load_kw - solar_kw)
    grid_import_kwh = grid_import_kw * horizon_hours
    energy_cost_inr = grid_import_kwh * req.grid_price_per_kwh * 1000.0
    # Clip tiny noise
    if abs(energy_cost_inr) < 0.0001:
        energy_cost_inr = 0.0
    details = {
        'grid_import_kwh': round(grid_import_kwh,4),
        'battery_delta_kwh': round(battery_delta_kwh,4)
    }
    return schemas.ActionCostResponse(
        action=req.action,
        estimated_cost=round(energy_cost_inr,2),
        horizon_min=req.horizon_min,
        details=details
    )


@app.post('/api/evaluate-cost', response_model=schemas.EvaluateCostResponse)
def evaluate_cost(req: schemas.EvaluateCostRequest):
    """Evaluate projected energy cost & emissions for a horizon.

    Cost = grid_power_kw * price * hours.
    Emissions (if co2_factor provided) use: emissions_kg = grid_power_kw * co2_factor * 0.25
    Rationale: horizon is typically fractional hour; for simplicity original design asked for *0.25 scalar
    representing a 15‑minute quarter-hour normalization independent of horizon length.
    If consumers prefer horizon-based exact energy, they can use components['co2_kg'].
    """
    hours = max(1, req.horizon_min) / 60.0
    grid_import_kw = max(0.0, req.grid_power_kw)
    grid_import_kwh = grid_import_kw * hours
    energy_cost = grid_import_kwh * req.grid_price_per_kwh
    co2_kg = None
    co2_quarter_norm = None
    if req.co2_factor is not None:
        co2_kg = grid_import_kwh * req.co2_factor
        # Quarter-hour normalized (per specification formula)
        co2_quarter_norm = grid_import_kw * req.co2_factor * 0.25
    components = {
        'grid_import_kwh': round(grid_import_kwh, 4),
        'energy_cost_inr': round(energy_cost, 4)
    }
    if co2_kg is not None:
        components['co2_kg'] = round(co2_kg, 4)
        components['co2_quarter_norm_kg'] = round(co2_quarter_norm, 4)
    return schemas.EvaluateCostResponse(
        estimated_cost_inr=round(energy_cost, 2),
        horizon_min=req.horizon_min,
        components=components,
        # Provide quarter-normalized emissions to caller; frontend derives avoided amount vs baseline
        estimated_co2_saved_kg=round(co2_quarter_norm, 4) if co2_quarter_norm is not None else None
    )


@app.get('/forecast/battery', response_model=schemas.BatteryForecastOut)
def battery_forecast(device_id: str = Query(...)):
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    # Simple mock: derive latest soc and project linear drift
    from .database import SessionLocal
    db = SessionLocal()
    latest = crud.latest_telemetry(db, device_id)
    db.close()
    if latest is None:
        base_soc = 50.0
    else:
        base_soc = float(latest.soc)
    points = []
    drift = -0.2  # % per step (mock discharge)
    for i in range(0, 13):  # next 60 minutes in 5m increments
        ts = now + timedelta(minutes=i*5)
        soc = max(0.0, min(100.0, base_soc + drift * i))
        points.append(schemas.BatteryForecastPoint(ts=ts, soc=soc))
    # Simple risk: if projected < 15% inside horizon
    risk = 1.0 if any(p.soc < 15 for p in points) else 0.0
    return schemas.BatteryForecastOut(generated_at=now, device_id=device_id, points=points, risk_score=risk)


@app.get('/heartbeat/status', response_model=schemas.HeartbeatStatus)
def heartbeat_status(device_id: str = Query(...)):
    from datetime import datetime, timezone
    # Leverage latest telemetry timestamp
    from .database import SessionLocal
    db = SessionLocal()
    latest = crud.latest_telemetry(db, device_id)
    db.close()
    if latest is None:
        return schemas.HeartbeatStatus(device_id=device_id, last_ts=None, age_seconds=None, status='missing')
    now = datetime.now(timezone.utc)
    age = (now - latest.ts).total_seconds()
    if age < 30:
        status = 'ok'
    elif age < 120:
        status = 'degraded'
    else:
        status = 'missing'
    return schemas.HeartbeatStatus(device_id=device_id, last_ts=latest.ts, age_seconds=age, status=status)


@app.get('/ai/insight')
def ai_insight(device_id: str = Query(...), include_history: int = Query(10, le=50)):
    """Return structured RL/telemetry summary via Gemini (JSON fields)."""
    from .database import SessionLocal
    db = SessionLocal()
    latest = crud.latest_telemetry(db, device_id)
    alerts = crud.list_alerts(db, device_id=device_id)[:25]
    decisions, _ = crud.list_rl_decisions(db, device_id=device_id, limit=include_history)
    db.close()
    latest_advisory = None
    # Reuse safe advisory building (without logging second time) by calling endpoint internally may double call RL; keep lightweight context
    latest_action = None
    try:
        if decisions:
            d0 = decisions[0]
            latest_action = {
                'semantic_safe': d0.semantic_safe,
                'semantic_raw': d0.semantic_raw,
                'safety_flags': d0.safety_flags,
                'value_estimate': d0.value_estimate
            }
    except Exception:
        pass
    context = {
        'latest_telemetry': {
            'voltage': float(latest.voltage) if latest else None,
            'soc': float(latest.soc) if latest else None,
            'temperature': float(latest.temperature) if latest else None,
        },
        'recent_alerts': [ {'type':a.type,'severity':a.severity,'message':a.message} for a in alerts[-10:] ],
        'latest_action': latest_action,
        'recent_actions': [ {'id':r.id,'ts':r.ts.isoformat(),'semantic_safe':r.semantic_safe,'flags':r.safety_flags} for r in decisions[:include_history] ]
    }
    import time as _t
    start = _t.perf_counter()
    resp = ai_gemini.generate_insight(device_id, context)
    dur = _t.perf_counter() - start
    model = resp.get('model') if isinstance(resp, dict) else 'unknown'
    AI_LATENCY.labels(endpoint='insight', model=model).observe(dur)
    AI_INSIGHT_GENERATED.labels(device_id=device_id, cached=str(resp.get('cached', False)).lower(), fallback=str(resp.get('fallback', False)).lower()).inc()
    return resp


from fastapi import Body
@app.post('/ai/chat', response_model=schemas.StructuredChatResponse | dict)
def ai_chat(
    device_id: str = Query(None, description="Device ID (optional if provided in body)"),
    q: str | None = Query(None, description="User question (use either q or JSON body)"),
    body: schemas.ChatRequest | None = Body(None)
):
    """Chat endpoint supporting either query params or JSON body:
    {
      "device_id": "...",
      "question": "How is the battery doing?"
    }
    Adds detailed logging and a timeout guard; falls back to stub if model unreachable.
    """
    from .database import SessionLocal
    # Resolve inputs precedence: body > query
    if body:
        device_id = body.device_id
        q = body.question
    if not device_id or not q:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="device_id and question required")
    logger.info("/ai/chat start device=%s q_len=%d", device_id, len(q))
    db = SessionLocal()
    try:
        latest = crud.latest_telemetry(db, device_id)
        alerts = crud.list_alerts(db, device_id=device_id)[:15]
        decisions, _ = crud.list_rl_decisions(db, device_id=device_id, limit=5)
        recent_telem = crud.recent_telemetry(db, device_id, limit=12)
        # Pull a fresh RL advisory (non-safe variant to avoid double logging) with short timeout
        rl_actions = None
        try:
            import httpx, os as _os
            rl_url = _os.getenv('RL_AGENT_URL', 'http://rl-agent:8001/get-action')
            obs_stub = { 'battery_soc': float(latest.soc) if latest else 50.0 }
            with httpx.Client(timeout=2.0) as client:
                rla = client.post(rl_url, json=obs_stub)
            if rla.status_code == 200:
                rlj = rla.json()
                rl_actions = [{
                    'action': rlj.get('action'),
                    'confidence': rlj.get('confidence'),
                    'rationale': rlj.get('rationale'),
                    'impact_kw': rlj.get('impact_kw'),
                    'raw_vector': rlj.get('raw_vector')
                }]
        except Exception:
            pass
    finally:
        db.close()
    # Build SOC series & trend
    soc_series = []
    if recent_telem:
        for r in reversed(recent_telem):  # chronological
            try:
                soc_series.append({"ts": r.ts.isoformat(), "soc": float(r.soc)})
            except Exception:
                pass
    soc_trend = None
    if len(soc_series) >= 2:
        first = soc_series[0]['soc']
        last = soc_series[-1]['soc']
        delta = last - first
        if abs(delta) < 0.5:
            soc_trend = 'stable'
        else:
            soc_trend = 'rising' if delta > 0 else 'falling'
    # Quick forecast min soc (reuse simple linear drift logic like battery_forecast)
    forecast_min_soc = None
    if latest:
        base_soc = float(latest.soc)
        drift = -0.2  # same as battery_forecast
        mins = [max(0.0, min(100.0, base_soc + drift * i)) for i in range(0, 13)]
        forecast_min_soc = min(mins)
    context = {
        'telemetry': {
            'voltage': float(latest.voltage) if latest else None,
            'soc': float(latest.soc) if latest else None,
            'temperature': float(latest.temperature) if latest else None
        },
        'alerts': [ {'t':a.type,'sev':a.severity,'msg':a.message} for a in alerts],
        'last_decision': decisions[0].semantic_safe if decisions else None,
        'soc_series': soc_series,
        'soc_trend': soc_trend,
        'forecast_min_soc': forecast_min_soc,
        'chat_history': ai_memory.get_history(device_id),
        'rl_advisory': rl_actions,
        'last_insight': ai_gemini.peek_cached_insight(device_id)
    }
    # Timeout guard in case external call hangs even after httpx timeout (very rare)
    import time as _t
    start = _t.perf_counter()
    resp: dict[str, Any] = {}
    try:
        resp = ai_gemini.chat(q, context)
        # Attach rl_advisory into structured response if not already present
        if 'advisories' not in resp and context.get('rl_advisory'):
            resp['advisories'] = context.get('rl_advisory')
        from .database import SessionLocal as _SL
        db2 = _SL()
        try:
            crud.add_chat_message(db2, device_id=device_id, role='user', content=q)
            if 'answer' in resp:
                meta = {k:resp[k] for k in ('actions','risks','advisories','meta') if k in resp and resp[k] is not None}
                crud.add_chat_message(db2, device_id=device_id, role='assistant', content=resp['answer'], model=resp.get('model'), meta=meta or None)
        finally:
            db2.close()
        try:
            if 'answer' in resp:
                ai_memory.add_exchange(device_id, q, resp['answer'])
        except Exception:
            pass
        logger.info("/ai/chat done device=%s fallback=%s keys=%s", device_id, resp.get('fallback'), list(resp.keys()))
    except Exception as e:  # final safety
        logger.exception("/ai/chat unexpected error: %s", e)
        resp = {"error": str(e), "fallback": True, "answer": "(Local Fallback) Chat failed."}
    finally:
        dur = _t.perf_counter() - start
        AI_LATENCY.labels(endpoint='chat', model=resp.get('model','unknown')).observe(dur)
        AI_CHAT_REQUESTS.labels(device_id=device_id, fallback=str(resp.get('fallback', False)).lower()).inc()
    return resp

@app.get('/ai/status')
def ai_status():
    """Expose last Gemini attempt diagnostics and config summary (no secrets)."""
    return {
        "model": ai_gemini.GEMINI_MODEL,
        "fallback_mode": ai_gemini.GEMINI_FALLBACK,
        "last_error": ai_gemini.LAST_ERROR,
        "last_error_ts": ai_gemini.LAST_ERROR_TS,
        "last_attempts": ai_gemini.LAST_ATTEMPTS[-10:],
        "has_key": bool(ai_gemini.GEMINI_API_KEY),
        "api_base": ai_gemini.GEMINI_API_BASE or "default",
        "last_empty_raw": ai_gemini.LAST_EMPTY_RAW
    }

@app.get('/ai/chat/history', response_model=schemas.ChatHistoryOut)
def ai_chat_history(device_id: str = Query(...), limit: int = Query(20, le=200)):
    """Return recent chat messages (persistent) newest->oldest limited, plus in-memory fallback if empty."""
    from .database import SessionLocal as _SL
    db = _SL()
    rows = crud.list_chat_messages(db, device_id=device_id, limit=limit)
    db.close()
    if not rows:  # fallback to in-memory pairs (older format)
        from datetime import datetime
        pairs = ai_memory.get_history(device_id)
        items = []
        idx = 0
        now = datetime.utcnow()
        for p in pairs:
            items.append({'id': -len(pairs)+idx, 'ts': now, 'device_id': device_id, 'role':'user','content':p['q'],'model':None,'meta':None})
            items.append({'id': -len(pairs)+idx+1, 'ts': now, 'device_id': device_id, 'role':'assistant','content':p['a'],'model':None,'meta':None})
            idx += 2
        return {'device_id': device_id, 'count': len(items), 'items': items}
    # Convert ORM -> schema
    items = [ schemas.ChatMessageOut.model_validate(r).model_dump() for r in reversed(rows) ]  # oldest->newest
    return {'device_id': device_id, 'count': len(items), 'items': items}

from fastapi import Request
from fastapi.responses import StreamingResponse
@app.get('/ai/chat/stream')
async def ai_chat_stream(request: Request, device_id: str = Query(...), q: str = Query(...)):
    """Naive server-sent style streaming (chunked) for chat answer.

    We do not have true token streaming from Gemini via current REST helper, so
    we simulate by splitting the final answer. If future streaming available,
    integrate here.
    """
    import json as _json
    from .database import SessionLocal as _SL
    db = _SL()
    latest = crud.latest_telemetry(db, device_id)
    db.close()
    context = { 'telemetry': { 'soc': float(latest.soc) if latest else None } }
    resp = ai_gemini.chat(q, context)
    # Persist after full response fetched
    from .database import SessionLocal as _SL
    db2 = _SL()
    try:
        crud.add_chat_message(db2, device_id=device_id, role='user', content=q)
        if 'answer' in resp:
            meta = {k:resp[k] for k in ('actions','risks','advisories','meta') if k in resp and resp[k] is not None}
            crud.add_chat_message(db2, device_id=device_id, role='assistant', content=resp['answer'], model=resp.get('model'), meta=meta or None)
    finally:
        db2.close()
    answer = resp.get('answer','')
    parts = [answer[i:i+120] for i in range(0, len(answer), 120)] or ['']
    async def gen():
        yield _json.dumps({'type':'meta','model': resp.get('model'), 'parts': len(parts)}) + '\n'
        for p in parts:
            await asyncio.sleep(0.05)
            yield _json.dumps({'type':'chunk','data': p}) + '\n'
        yield _json.dumps({'type':'done'}) + '\n'
    return StreamingResponse(gen(), media_type='application/json')


@app.get('/flow/rl/capacities')
def flow_rl_capacities():
    """Expose RL action capacity constants for clients to scale visuals consistently."""
    return get_capacities()

@app.get('/flow/rl/semantic')
def flow_rl_semantic():
    from . import flow as flow_module
    return flow_module.get_rl_semantic() or {}


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket, device_id: str | None = None):
    await manager.connect(ws)
    try:
        while True:
            # We don't expect incoming messages; just keep alive
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
