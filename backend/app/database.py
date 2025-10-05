import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DB_USER = os.getenv("DB_USER", "iot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "iotpass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "iotdb")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    # Import models so metadata is populated
    from . import models  # noqa: F401
    with engine.begin() as conn:
        # Enable TimescaleDB extension & ensure telemetry hypertable exists.
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))

        # Detect if telemetry already a hypertable
        hypertable_exists = conn.execute(text(
            "SELECT 1 FROM _timescaledb_catalog.hypertable WHERE table_name='telemetry'"
        )).first() is not None

        if not hypertable_exists:
            # Drop any legacy table (prototype: data loss acceptable)
            conn.execute(text("DROP TABLE IF EXISTS telemetry CASCADE;"))
            # Create base table WITHOUT constraints first
            conn.execute(text(
                """
                CREATE TABLE telemetry (
                    device_id text NOT NULL,
                    ts timestamptz NOT NULL DEFAULT now(),
                    voltage numeric,
                    soc numeric,
                    temperature numeric
                );
                """
            ))
            # Convert to hypertable BEFORE adding PK (avoids unique index error)
            conn.execute(text("SELECT create_hypertable('telemetry', 'ts', if_not_exists => TRUE);"))
            # Now add composite PK including partition column
            conn.execute(text("ALTER TABLE telemetry ADD CONSTRAINT pk_telemetry_device_ts PRIMARY KEY (device_id, ts);"))
        else:
            # Ensure ts column has default now() even on existing tables
            try:
                conn.execute(text("ALTER TABLE telemetry ALTER COLUMN ts SET DEFAULT now();"))
            except Exception:
                pass

        # Ensure remaining tables exist
        models.Device.__table__.create(bind=conn, checkfirst=True)
        models.Alert.__table__.create(bind=conn, checkfirst=True)
        models.RLDecisionLog.__table__.create(bind=conn, checkfirst=True)
        models.ChatMessage.__table__.create(bind=conn, checkfirst=True)
        # Migration: add ack_ts column if missing (demo-safe)
        try:
            conn.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS ack_ts TIMESTAMP"))
        except Exception:
            pass
        # Seed default device
        default_device_id = os.getenv("DEFAULT_DEVICE_ID", "11111111-1111-1111-1111-111111111111")
        conn.execute(text("""
            INSERT INTO devices (id, name)
            VALUES (:id, 'Demo Battery Pack')
            ON CONFLICT (id) DO NOTHING;
        """), {"id": default_device_id})


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
