from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Integer, Text, PrimaryKeyConstraint, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    telemetry = relationship("Telemetry", back_populates="device")
    alerts = relationship("Alert", back_populates="device")


class Telemetry(Base):
    __tablename__ = "telemetry"
    device_id = Column(String, ForeignKey("devices.id"), index=True, nullable=False)
    ts = Column(DateTime(timezone=True), default=datetime.utcnow, index=True, nullable=False)
    voltage = Column(Numeric)
    soc = Column(Numeric)
    temperature = Column(Numeric)
    __table_args__ = (
        PrimaryKeyConstraint('device_id', 'ts', name='pk_telemetry_device_ts'),
    )
    device = relationship("Device", back_populates="telemetry")


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("devices.id"), index=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    value = Column(Numeric)
    threshold = Column(Numeric)
    ack_ts = Column(DateTime, nullable=True, index=True)
    device = relationship("Device", back_populates="alerts")


class RLDecisionLog(Base):
    __tablename__ = 'rl_decision_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    device_id = Column(String, index=True, nullable=False)
    obs = Column(JSON, nullable=False)  # Full observation vector
    raw_vector = Column(JSON, nullable=True)
    semantic_raw = Column(JSON, nullable=True)
    semantic_safe = Column(JSON, nullable=True)
    safety_flags = Column(JSON, nullable=True)
    value_estimate = Column(Numeric, nullable=True)


class ChatMessage(Base):
    """Persistent chat history (simple audit log for AI interactions).

    We persist both user and assistant messages. "meta" can hold structured
    fields (actions, risks, etc.) for assistant replies.
    """
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    device_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    model = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)

