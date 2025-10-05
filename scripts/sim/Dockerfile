FROM python:3.11-slim
WORKDIR /sim
RUN pip install --no-cache-dir paho-mqtt==2.1.0 requests==2.32.3
COPY device_sim.py ./
CMD ["python", "device_sim.py"]
