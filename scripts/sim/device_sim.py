import os
import json
import time
import random
import paho.mqtt.client as mqtt
import requests

BROKER = os.getenv("MQTT_BROKER_HOST", "localhost")
PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
DEVICE_ID = os.getenv("DEVICE_ID", "11111111-1111-1111-1111-111111111111")
BACKEND_HTTP = os.getenv("BACKEND_HTTP_URL")  # e.g. http://backend:8000

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

print(f"Simulator started for device {DEVICE_ID} -> {BROKER}:{PORT}")

soc = 55.0
voltage = 230.0
temperature = 30.0

while True:
    # Simple dynamics
    soc -= random.uniform(0.05, 0.4)
    if soc < 5:
        soc = 100  # recharge
    voltage += random.uniform(-0.8, 0.8)
    temperature += random.uniform(-0.3, 0.4)
    if temperature < 25: temperature = 25
    if temperature > 70: temperature = 50
    # Generate a consistent timestamp so MQTT & HTTP (if both enabled) can be de-duplicated.
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    payload = {"voltage": round(voltage,2), "soc": round(soc,2), "temperature": round(temperature,2), "ts": ts}
    topic = f"devices/{DEVICE_ID}/telemetry"
    client.publish(topic, json.dumps(payload), qos=0, retain=False)
    print("Published", topic, payload)
    # HTTP fallback
    if BACKEND_HTTP:
        try:
            r = requests.post(f"{BACKEND_HTTP}/telemetry", json={"device_id": DEVICE_ID, **payload}, timeout=3)
            if r.status_code != 200:
                print("HTTP POST failed", r.status_code, r.text[:120])
        except Exception as e:
            print("HTTP POST error", e)
    time.sleep(2)
