from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class DeviceOut(BaseModel):
    id: str
    name: str
    class Config:
        from_attributes = True


class TelemetryIn(BaseModel):
    device_id: str
    voltage: float
    soc: float
    temperature: float


class TelemetryOut(TelemetryIn):
    ts: datetime
    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    device_id: str
    ts: datetime
    type: str
    severity: str
    message: str
    value: float | None = None
    threshold: float | None = None
    ack_ts: datetime | None = None
    class Config:
        from_attributes = True


class SmartAlertOut(AlertOut):
    recommended_action: str | None = None
    risk_generated: bool | None = None


class RLActionOut(BaseModel):
    id: str
    title: str
    description: str
    impact_kw: float
    confidence: float
    horizon_min: int
    raw_vector: list[float] | None = None
    value_estimate: float | None = None
    semantic_raw: dict | None = None
    semantic_safe: dict | None = None
    safety_flags: list[str] | None = None


class RLAdvisoryOut(BaseModel):
    generated_at: datetime
    device_id: str
    actions: list[RLActionOut]
    model_version: str | None = None


class RLSafeAdvisoryOut(RLAdvisoryOut):
    """Alias schema (same fields) reserved for semantic/safety endpoint clarity."""
    pass


class RLDecisionHistoryItem(BaseModel):
    id: int
    ts: datetime
    value_estimate: float | None = None
    safety_flags: list[str] | None = None
    semantic_safe: dict | None = None
    semantic_raw: dict | None = None
    semantic_delta: dict | None = None  # numeric (raw - safe) diffs for quick inspection


class RLDecisionHistoryOut(BaseModel):
    device_id: str
    decisions: list[RLDecisionHistoryItem]
    next_before_id: int | None = None  # pagination cursor (pass as before_id to fetch older)
    has_more: bool = False


class ActionCostRequest(BaseModel):
    device_id: str
    action: str  # e.g., DISCHARGE_BATTERY_TO_LOAD, CHARGE_BATTERY, HOLD
    battery_soc: float
    solar_output_kw: float
    grid_price_per_kwh: float
    current_load_kw: float
    horizon_min: int = 15


class ActionCostResponse(BaseModel):
    action: str
    estimated_cost: float
    horizon_min: int
    currency: str = "INR"
    details: dict[str, float] | None = None


class EvaluateCostRequest(BaseModel):
    grid_power_kw: float
    grid_price_per_kwh: float
    horizon_min: int = 15
    co2_factor: float | None = None  # kg CO2 per kWh (optional)


class EvaluateCostResponse(BaseModel):
    estimated_cost_inr: float
    horizon_min: int
    components: dict[str, float] | None = None
    # For each scenario this represents absolute emissions (kg) for the horizon; frontend derives savings vs baseline
    estimated_co2_saved_kg: float | None = None


class BatteryForecastPoint(BaseModel):
    ts: datetime
    soc: float


class BatteryForecastOut(BaseModel):
    generated_at: datetime
    device_id: str
    points: list[BatteryForecastPoint]
    method: str = "mock-linear"
    risk_score: float | None = None


class HeartbeatStatus(BaseModel):
    device_id: str
    last_ts: datetime | None
    age_seconds: float | None
    status: str  # ok | degraded | missing


class AckResponse(BaseModel):
    id: int
    ack_ts: datetime


class HealthStatus(BaseModel):
    status: str = Field(default="ok")


class ChatRequest(BaseModel):
    device_id: str
    question: str


class ChatMessageOut(BaseModel):
    id: int
    ts: datetime
    device_id: str
    role: str
    content: str
    model: str | None = None
    meta: dict | None = None
    class Config:
        from_attributes = True


class ChatHistoryOut(BaseModel):
    device_id: str
    count: int
    items: list[ChatMessageOut]


class StructuredChatResponse(BaseModel):
    answer: str
    actions: list[dict] | None = None
    risks: list[dict] | None = None
    advisories: dict | None = None
    meta: dict | None = None
    model: str | None = None
    fallback: bool | None = None
    error: str | None = None
