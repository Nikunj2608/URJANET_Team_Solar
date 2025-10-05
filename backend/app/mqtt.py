import json
import logging
import os
import threading
import time
import random
from typing import Callable, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTIngestor:
    """Robust MQTT ingestion helper.

    Features added:
    - Configurable topic pattern & QoS via env.
    - Automatic exponential backoff reconnect loop.
    - Basic ingestion counters (messages_ok, messages_failed, last_message_ts).
    - Optional catch-all subscription only when DEBUG_MQTT_ALL=1.
    - Graceful stop() to allow clean test shutdown.
    """

    def __init__(self, on_telemetry: Callable[[dict], None]):
        self.host = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.topic = os.getenv("MQTT_SUB_TOPIC", "devices/+/telemetry")
        self.qos = int(os.getenv("MQTT_QOS", "0"))
        self.debug_all = os.getenv("DEBUG_MQTT_ALL", "0") == "1"
        self.client = mqtt.Client()
        self.client.on_log = self._on_log
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.on_telemetry = on_telemetry
        self._loop_started = False
        self._stopping = False
        # Simple stats
        self.messages_ok = 0
        self.messages_failed = 0
        self.last_message_ts: Optional[float] = None

    def start(self):
        if self._loop_started:
            return
        self._loop_started = True
        try:
            self.client.enable_logger(logger)
        except Exception:  # pragma: no cover
            pass
        threading.Thread(target=self._connect_loop, name="mqtt-connect", daemon=True).start()
        self.client.loop_start()

    def stop(self):
        self._stopping = True
        try:
            self.client.disconnect()
        except Exception:  # pragma: no cover
            pass
        if self._loop_started:
            self.client.loop_stop()

    def _connect_loop(self):
        backoff = 1.0
        while not self._stopping:
            try:
                logger.info("MQTT attempting connect %s:%s", self.host, self.port)
                rc = self.client.connect(self.host, self.port, keepalive=60)
                if rc == 0:
                    logger.info("MQTT connect() initiated successfully")
                    return
                else:  # pragma: no cover
                    logger.warning("MQTT connect rc=%s (retrying)", rc)
            except Exception as e:  # pragma: no cover
                logger.warning("MQTT connection error: %s", e)
            time.sleep(backoff + random.uniform(0, 0.25))
            backoff = min(backoff * 2, 30)

    # paho-mqtt 1.6.x legacy signature
    def _on_connect(self, client, userdata, flags, rc):  # type: ignore[override]
        if rc == 0:
            logger.info("MQTT connected; subscribing topic=%s qos=%s", self.topic, self.qos)
            res1, mid1 = client.subscribe(self.topic, qos=self.qos)
            logger.info("Subscription %s result=%s mid=%s", self.topic, res1, mid1)
            if self.debug_all and self.topic != "#":
                res2, mid2 = client.subscribe("#", qos=0)
                logger.info("Debug subscription # result=%s mid=%s", res2, mid2)
        else:
            logger.error("MQTT connect failed rc=%s", rc)

    def _on_message(self, client, userdata, msg):  # type: ignore[override]
        topic = msg.topic
        try:
            payload = msg.payload.decode()
            logger.debug("MQTT received topic=%s payload=%s", topic, payload)
            data = json.loads(payload)
            # Extract device_id from topic parts
            parts = topic.split('/')
            if len(parts) >= 2:
                data.setdefault('device_id', parts[1])
            self.on_telemetry(data)
            self.messages_ok += 1
            self.last_message_ts = time.time()
        except Exception as e:
            self.messages_failed += 1
            logger.warning("Failed to process MQTT message on %s: %s", topic, e)

    def _on_log(self, client, userdata, level, buf):  # type: ignore[override]
        logger.debug("MQTT log level=%s msg=%s", level, buf)

    # --- Introspection helpers ---
    def stats(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "topic": self.topic,
            "qos": self.qos,
            "messages_ok": self.messages_ok,
            "messages_failed": self.messages_failed,
            "last_message_ts": self.last_message_ts,
        }
