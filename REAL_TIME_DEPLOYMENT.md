# 📡 Real-Time Deployment Guide: Handling New Incoming Data

## Overview
You trained the RL model on **past 10 years of data**. Now you want to deploy it to handle **new incoming data in real-time**. This guide explains how.

---

## 🤔 The Big Question: "What About New Data?"

### **Current State**: Trained on Past Data
```
Training Data (2015-2025): [●●●●●●●●●●] ← Model learned from this
                           10 years
```

### **Deployment Goal**: Handle New Data
```
Real-Time Operation:  ────●────●────●────●────> Time
                        15min 30min 45min 1hr
                        New   New   New   New
                        data  data  data  data
```

**Your questions**:
1. ❓ Does the model need to be retrained for every new data point?
2. ❓ How does it handle data it has never seen?
3. ❓ What if solar/wind patterns change over time?
4. ❓ How do we connect to real sensors?

---

## ✅ Answer: No Retraining Needed (Usually)

### **How RL Models Work in Production**

**Training Phase** (What you already did):
```python
# You trained for 1000 episodes
for episode in range(1000):
    obs = env.reset()
    for step in range(96):  # 24 hours
        action = agent.select_action(obs)
        next_obs, reward, done, info = env.step(action)
        # Agent learned patterns
```

**Deployment Phase** (What happens now):
```python
# Load trained model
agent.load("models/best_model.pt")

# Run forever on new data
while True:
    # Get CURRENT state from real sensors
    obs = get_current_state_from_sensors()  # NEW DATA!
    
    # Agent makes decision (NO TRAINING!)
    action = agent.select_action(obs, deterministic=True)
    
    # Send action to real hardware
    execute_action_on_microgrid(action)
    
    # Wait 15 minutes
    time.sleep(15 * 60)
```

**Key insight**: 
- ✅ Model uses learned patterns to handle new data
- ✅ No retraining needed for normal operation
- ✅ Just feed new observations → get actions

---

## 🧠 Why It Works: Generalization

### **What Model Learned** (During Training):
```
Pattern Recognition:
• "High solar + low price → Charge battery"
• "Evening + high price → Discharge battery"
• "Low SoC + no renewable → Charge from grid"
• "High SoC + excess solar → Export to grid"
```

### **What Model Does** (With New Data):
```
New situation: Solar = 1,800 kW, Price = ₹2.50/kWh, Battery SoC = 40%

Model thinks:
1. "I've seen similar situations in training"
2. "Solar is high (like pattern #1)"
3. "Price is low (like pattern #1)"
4. "Battery has room (SoC < 80%)"
5. → Decision: Charge battery at 600 kW ✓

This is NEW data, but model recognizes the PATTERN.
```

---

## 📊 Deployment Architecture

### **System Overview**

```
┌──────────────────────────────────────────────────────────────────┐
│                     PHYSICAL MICROGRID                           │
│                                                                  │
│  [Solar] [Wind] [Battery] [Grid] [Load] [EVs]                  │
│     ↓      ↓       ↓        ↓       ↓      ↓                   │
│  ┌────────────────────────────────────────────┐                │
│  │         SENSORS & METERS                    │                │
│  │  (Measure real-time power, voltage, SoC)   │                │
│  └────────────────────────────────────────────┘                │
└───────────────────────┬──────────────────────────────────────────┘
                        │ Data (every 15 min or 1 sec)
                        ↓
┌───────────────────────────────────────────────────────────────────┐
│                   DATA ACQUISITION LAYER                          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  SCADA/IoT   │  │  Weather API │  │  Grid Price  │          │
│  │  (Modbus)    │  │  (Solar/Wind)│  │  API         │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────┬───────────────────────────────────────────┘
                        │ Raw sensor data
                        ↓
┌───────────────────────────────────────────────────────────────────┐
│                   DATA PREPROCESSING                              │
│                                                                   │
│  • Validate data (check for outliers/errors)                     │
│  • Normalize (same scale as training data)                       │
│  • Create observation vector (90 dimensions)                     │
│  • Add forecasts (2-hour ahead prediction)                       │
└───────────────────────┬───────────────────────────────────────────┘
                        │ obs = [90 values]
                        ↓
┌───────────────────────────────────────────────────────────────────┐
│                   RL AGENT (Your Trained Model)                   │
│                                                                   │
│  model = load("best_model.pt")                                   │
│  action = model.predict(obs)    ← NO TRAINING HERE!             │
│                                                                   │
│  action = [battery_1, battery_2, grid, ev, curtail]             │
└───────────────────────┬───────────────────────────────────────────┘
                        │ Control commands
                        ↓
┌───────────────────────────────────────────────────────────────────┐
│                   SAFETY SUPERVISOR                               │
│                                                                   │
│  • Check if action violates safety limits                        │
│  • Clamp to safe ranges                                          │
│  • Log any violations                                            │
└───────────────────────┬───────────────────────────────────────────┘
                        │ Safe action
                        ↓
┌───────────────────────────────────────────────────────────────────┐
│                   CONTROL EXECUTION LAYER                         │
│                                                                   │
│  • Send commands to battery inverters                            │
│  • Control grid connection                                       │
│  • Manage EV chargers                                            │
│  • Apply curtailment to renewables                               │
└───────────────────────┬───────────────────────────────────────────┘
                        │ Physical actions
                        ↓
        [Battery charges/discharges, grid import/export, etc.]
```

---

## 🔧 Implementation: 3 Deployment Modes

### **Mode 1: Simulation (Testing)**
Use for: Testing your model before deploying to real hardware

```python
# deployment/simulation_mode.py

import torch
import pandas as pd
from train_ppo_improved import ImprovedPPOAgent
from microgrid_env import MicrogridEMSEnv

# Load trained model
agent = ImprovedPPOAgent(obs_dim=90, action_dim=5)
agent.load("models/best_model.pt")

# Load NEW data (e.g., 2026 data, model never saw this!)
new_pv = pd.read_csv('data/NEW_2026_pv.csv')
new_wt = pd.read_csv('data/NEW_2026_wt.csv')
new_load = pd.read_csv('data/NEW_2026_load.csv')
new_price = pd.read_csv('data/NEW_2026_price.csv')

# Create environment with NEW data
env = MicrogridEMSEnv(new_pv, new_wt, new_load, new_price)

# Run for 1 day (96 steps)
obs = env.reset()
total_cost = 0

for step in range(96):
    # Agent makes decision (NO TRAINING!)
    action = agent.select_action(obs, deterministic=True)
    
    # Environment processes action
    next_obs, reward, done, info = env.step(action)
    
    # Log results
    total_cost += info['cost']
    print(f"Step {step}: Cost = ₹{info['cost']:.2f}, "
          f"Emissions = {info['emissions']:.2f} kg")
    
    obs = next_obs
    
    if done:
        break

print(f"\nTotal cost: ₹{total_cost:.2f}")
```

**Key points**:
- ✅ Model sees NEW data (2026, not in training)
- ✅ No training happens (model frozen)
- ✅ Tests if model generalizes well

---

### **Mode 2: Real-Time (Production)**
Use for: Deploying to actual hardware

```python
# deployment/realtime_mode.py

import torch
import time
from datetime import datetime
from train_ppo_improved import ImprovedPPOAgent
from safety_supervisor import SafetySupervisor
import requests  # For API calls

# ===== INITIALIZATION =====

# Load trained model
agent = ImprovedPPOAgent(obs_dim=90, action_dim=5)
agent.load("models/best_model.pt")

# Load safety supervisor
safety = SafetySupervisor()

# Initialize normalizer (MUST use same stats from training!)
normalizer_mean = torch.load("models/best_model_normalizer_mean.pt")
normalizer_std = torch.load("models/best_model_normalizer_std.pt")

# ===== DATA COLLECTION FUNCTIONS =====

def get_solar_power():
    """Get current solar generation from sensor"""
    # Option 1: Read from SCADA system
    response = requests.get("http://microgrid-scada/api/solar/power")
    return response.json()['power_kw']
    
    # Option 2: Read from IoT device (e.g., Modbus)
    # from pymodbus.client import ModbusTcpClient
    # client = ModbusTcpClient('192.168.1.100')
    # result = client.read_holding_registers(0, 1)
    # return result.registers[0] / 10  # Convert to kW

def get_wind_power():
    """Get current wind generation from sensor"""
    response = requests.get("http://microgrid-scada/api/wind/power")
    return response.json()['power_kw']

def get_load_power():
    """Get current load from sensor"""
    response = requests.get("http://microgrid-scada/api/load/power")
    return response.json()['power_kw']

def get_battery_state():
    """Get battery SoC and SoH"""
    response = requests.get("http://microgrid-scada/api/battery/status")
    data = response.json()
    return data['soc'], data['soh']

def get_grid_price():
    """Get current grid price"""
    response = requests.get("http://utility-api/api/price/current")
    return response.json()['price_per_kwh']

def get_weather_forecast():
    """Get 2-hour ahead weather forecast"""
    response = requests.get("http://weather-api/forecast?hours=2")
    data = response.json()
    return {
        'solar_forecast': data['solar_irradiance'],
        'wind_forecast': data['wind_speed']
    }

def construct_observation():
    """Construct 90-dim observation vector from sensors"""
    
    # Get current measurements
    solar_power = get_solar_power()
    wind_power = get_wind_power()
    load_power = get_load_power()
    soc, soh = get_battery_state()
    price = get_grid_price()
    forecast = get_weather_forecast()
    
    # Get temporal features
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    day_of_week = now.weekday()
    
    # Build observation (must match training format!)
    obs = [
        # Temporal (10 dims)
        hour / 24.0,                    # Normalized hour
        minute / 60.0,                  # Normalized minute
        day_of_week / 7.0,              # Normalized day
        np.sin(2 * np.pi * hour / 24),  # Hour sin
        np.cos(2 * np.pi * hour / 24),  # Hour cos
        # ... (5 more temporal features)
        
        # PV (10 dims)
        solar_power / 3000.0,           # Normalized current
        forecast['solar_forecast'][0] / 3000.0,  # +15 min
        forecast['solar_forecast'][1] / 3000.0,  # +30 min
        # ... (7 more PV features)
        
        # Wind (10 dims)
        wind_power / 1000.0,
        # ... (9 more wind features)
        
        # Load (10 dims)
        load_power / 2000.0,
        # ... (9 more load features)
        
        # Battery (20 dims)
        soc,  # Already 0-1
        soh,
        # ... (18 more battery features)
        
        # Grid (10 dims)
        price / 10.0,  # Normalize price
        # ... (9 more grid features)
        
        # EV (10 dims)
        # ... (10 EV features)
        
        # Health (10 dims)
        # ... (10 health features)
        
        # Previous actions (10 dims)
        # ... (10 action history features)
    ]
    
    return np.array(obs, dtype=np.float32)

def execute_action(action):
    """Send action to physical hardware"""
    
    battery_1_power = action[0]  # kW
    battery_2_power = action[1]
    grid_power = action[2]
    ev_power = action[3]
    curtailment = action[4]
    
    # Send to battery inverter
    requests.post("http://microgrid-scada/api/battery1/setpower", 
                  json={'power_kw': battery_1_power})
    requests.post("http://microgrid-scada/api/battery2/setpower",
                  json={'power_kw': battery_2_power})
    
    # Send to grid controller
    requests.post("http://microgrid-scada/api/grid/setpower",
                  json={'power_kw': grid_power})
    
    # Send to EV charger
    requests.post("http://microgrid-scada/api/ev/setpower",
                  json={'power_kw': ev_power})
    
    # Send curtailment command
    requests.post("http://microgrid-scada/api/renewable/curtail",
                  json={'curtail_ratio': curtailment})

# ===== MAIN CONTROL LOOP =====

def main():
    print("🚀 Starting RL Agent in REAL-TIME MODE")
    print("⏰ Control interval: 15 minutes")
    print("─" * 60)
    
    while True:
        try:
            # 1. Get current state from sensors
            obs = construct_observation()
            
            # 2. Normalize (CRITICAL! Must match training)
            obs_normalized = (obs - normalizer_mean) / (normalizer_std + 1e-8)
            
            # 3. Agent makes decision
            action = agent.select_action(obs_normalized, deterministic=True)
            
            # 4. Safety check
            action_safe, violations = safety.check_and_correct(action, obs)
            
            if violations:
                print(f"⚠️  Safety violations detected: {violations}")
            
            # 5. Execute action
            execute_action(action_safe)
            
            # 6. Log
            timestamp = datetime.now().isoformat()
            print(f"✓ {timestamp}: Action executed")
            print(f"  Battery: {action_safe[0]:.1f} kW, {action_safe[1]:.1f} kW")
            print(f"  Grid: {action_safe[2]:.1f} kW")
            print(f"  EV: {action_safe[3]:.1f} kW")
            
            # 7. Wait 15 minutes
            time.sleep(15 * 60)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Reverting to safe mode (no action)")
            time.sleep(60)  # Wait 1 min before retry

if __name__ == "__main__":
    main()
```

**Key features**:
- ✅ Reads from real sensors every 15 min
- ✅ Uses trained model (no training)
- ✅ Sends commands to real hardware
- ✅ Safety checks before execution
- ✅ Error handling (falls back to safe mode)

---

### **Mode 3: Hybrid (Real-Time + Online Learning)**
Use for: Adapting to changing patterns over time

```python
# deployment/hybrid_mode.py

import torch
from collections import deque

# Load trained model
agent = ImprovedPPOAgent(obs_dim=90, action_dim=5)
agent.load("models/best_model.pt")

# Replay buffer for online learning
replay_buffer = deque(maxlen=10000)

# Thresholds for retraining
RETRAIN_THRESHOLD = 1000  # Retrain after 1000 new samples
PERFORMANCE_DROP_THRESHOLD = 0.2  # 20% worse than baseline

step_count = 0
baseline_performance = -53585  # From training

while True:
    # Get observation
    obs = construct_observation()
    
    # Agent acts
    action = agent.select_action(obs, deterministic=True)
    
    # Execute
    execute_action(action)
    
    # Wait and get result
    time.sleep(15 * 60)
    next_obs = construct_observation()
    reward = calculate_reward()  # Compute actual reward
    
    # Store experience
    replay_buffer.append((obs, action, reward, next_obs))
    step_count += 1
    
    # Check if we need to retrain
    if step_count >= RETRAIN_THRESHOLD:
        recent_performance = np.mean([r for _, _, r, _ in replay_buffer])
        
        if recent_performance < baseline_performance * (1 - PERFORMANCE_DROP_THRESHOLD):
            print("⚠️  Performance dropped! Retraining...")
            
            # Retrain on recent data
            agent.train_on_buffer(replay_buffer, epochs=10)
            
            # Save new model
            agent.save("models/best_model_updated.pt")
            
            baseline_performance = recent_performance
            step_count = 0
```

**When to use this**:
- ⚠️ When microgrid characteristics change (new equipment)
- ⚠️ When weather patterns shift (climate change)
- ⚠️ When price structure changes (new tariffs)

**Caution**: Only retrain if performance degrades significantly!

---

## 📡 Data Sources: Where New Data Comes From

### **1. SCADA System** (Supervisory Control and Data Acquisition)
```
Industrial standard for microgrid monitoring
• Protocols: Modbus TCP/RTU, DNP3, IEC 61850
• Frequency: 1-second resolution
• Data: Real-time power, voltage, current, frequency
```

**Example**: Reading from Modbus
```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.100', port=502)
result = client.read_holding_registers(address=0, count=10)

solar_power = result.registers[0] / 10  # kW
wind_power = result.registers[1] / 10
battery_soc = result.registers[2] / 100  # 0-1
```

### **2. IoT Sensors**
```
Low-cost sensors for monitoring
• Protocols: MQTT, HTTP REST API
• Frequency: 10-second to 1-minute
• Data: Temperature, irradiance, wind speed
```

**Example**: Reading from MQTT
```python
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    if msg.topic == "microgrid/solar/power":
        solar_power = float(msg.payload)
        # Use this value

client = mqtt.Client()
client.on_message = on_message
client.connect("mqtt.broker.com", 1883)
client.subscribe("microgrid/#")
client.loop_forever()
```

### **3. Weather APIs**
```
For forecasting (needed by your RL model)
• Services: OpenWeatherMap, NREL NSRDB, Visual Crossing
• Frequency: Every 15 minutes
• Data: 2-hour ahead solar irradiance, wind speed
```

**Example**: OpenWeatherMap API
```python
import requests

API_KEY = "your_api_key"
lat, lon = 28.6139, 77.2090  # Delhi

response = requests.get(
    f"https://api.openweathermap.org/data/2.5/forecast",
    params={'lat': lat, 'lon': lon, 'appid': API_KEY}
)

data = response.json()
next_2h_irradiance = [d['clouds']['all'] for d in data['list'][:2]]
```

### **4. Grid Price APIs**
```
For real-time pricing
• India: IEX (Indian Energy Exchange), POSOCO
• Frequency: Every 15 minutes
• Data: Current price, day-ahead prices
```

### **5. Database (Historical Storage)**
```
Store all data for analysis
• Time-series DB: InfluxDB, TimescaleDB
• Frequency: Every 15 minutes
• Purpose: Logs, analysis, retraining data
```

---

## 🔄 Data Flow Timeline

### **Typical 15-Minute Cycle**:

```
00:00 ────> Get sensor data (5 sec)
            • Solar: 1,234 kW
            • Wind: 345 kW
            • Load: 1,567 kW
            • Battery SoC: 67%
            • Price: ₹4.50/kWh

00:05 ────> Preprocess (2 sec)
            • Normalize
            • Add forecasts
            • Build observation vector

00:07 ────> RL Agent decision (<1 sec)
            • action = model.predict(obs)
            • action = [450, 150, 0, 200, 0]

00:08 ────> Safety check (1 sec)
            • Verify limits
            • Clamp if needed

00:09 ────> Execute action (5 sec)
            • Send to battery inverter
            • Send to grid controller
            • Send to EV charger

00:14 ────> Log results (1 sec)
            • Save to database
            • Update dashboard

00:15 ────> Wait for next cycle...

15:00 ────> Repeat!
```

---

## 🚨 Handling Edge Cases

### **Case 1: Sensor Failure**
```python
def get_solar_power_safe():
    try:
        return get_solar_power()
    except:
        # Fallback: Use forecast
        print("⚠️  Solar sensor failed, using forecast")
        return get_solar_forecast()
```

### **Case 2: Network Outage**
```python
# Store actions locally, execute when connection restored
action_queue = []

def execute_action_safe(action):
    try:
        execute_action(action)
    except requests.exceptions.ConnectionError:
        print("⚠️  Network down, queuing action")
        action_queue.append((time.time(), action))
```

### **Case 3: Model Predicts Unsafe Action**
```python
# Safety supervisor ALWAYS checks
action_safe, violations = safety.check_and_correct(action, obs)

if violations:
    # Log incident
    log_safety_violation(violations)
    
    # Alert operator
    send_alert("Model predicted unsafe action, corrected by safety system")
```

### **Case 4: Extreme Weather (Out of Distribution)**
```python
def is_observation_valid(obs):
    """Check if observation is within training distribution"""
    
    solar_power = obs[10]  # Normalized
    
    # Check if way outside training range
    if solar_power > 1.5 or solar_power < -0.5:
        print("⚠️  Observation outside training distribution!")
        return False
    
    return True

# In main loop
if not is_observation_valid(obs):
    print("🛑 Switching to rule-based controller")
    action = baseline_controller(obs)  # Fallback
else:
    action = agent.select_action(obs)
```

---

## 📊 Monitoring & Logging

### **What to Log** (Every 15 min):

```python
log_entry = {
    'timestamp': datetime.now().isoformat(),
    
    # Inputs
    'observation': obs.tolist(),
    'solar_power': solar_power,
    'wind_power': wind_power,
    'load_power': load_power,
    'battery_soc': soc,
    'grid_price': price,
    
    # Outputs
    'action': action.tolist(),
    'action_safe': action_safe.tolist(),
    
    # Results
    'reward': reward,
    'cost': cost,
    'emissions': emissions,
    'safety_violations': violations,
    
    # System health
    'model_inference_time_ms': inference_time,
    'sensor_errors': sensor_errors,
}

# Save to database
save_to_influxdb(log_entry)

# Also save to CSV backup
with open('logs/realtime_log.csv', 'a') as f:
    writer = csv.DictWriter(f, fieldnames=log_entry.keys())
    writer.writerow(log_entry)
```

---

## 🔄 When to Retrain (and When NOT To)

### ✅ **RETRAIN** if:
1. **Performance drops >20%** for >1 week
2. **Major equipment change** (new battery, new solar panel)
3. **Tariff structure changes** (different pricing)
4. **Seasonal shifts** (monsoon vs summer patterns)
5. **After 6-12 months** (periodic refresh)

### ❌ **DON'T RETRAIN** if:
1. **Normal weather variation** (cloudy day is fine!)
2. **Short-term performance dip** (<1 week)
3. **Sensor glitches** (fix sensor, not model)
4. **Model works fine** (if it ain't broke...)

### **Retraining Process**:
```python
# 1. Collect new data (at least 1 month)
new_data = collect_last_30_days()

# 2. Combine with old training data
combined_data = pd.concat([old_training_data, new_data])

# 3. Retrain (maybe fewer episodes since starting from good model)
agent.load("models/best_model.pt")  # Start from current
train(agent, combined_data, episodes=200)  # Fine-tune

# 4. Validate on held-out test set
test_performance = evaluate(agent, test_data)

# 5. Only deploy if better
if test_performance > current_performance:
    agent.save("models/best_model_v2.pt")
    print("✓ New model deployed")
else:
    print("✗ New model worse, keeping old one")
```

---

## 🚀 Deployment Checklist

### **Before Going Live**:

- [ ] ✅ Model trained and validated
- [ ] ✅ Safety supervisor configured
- [ ] ✅ Normalizer stats saved (mean/std from training)
- [ ] ✅ Sensor APIs tested and working
- [ ] ✅ Action execution tested (on test bench)
- [ ] ✅ Logging system set up
- [ ] ✅ Dashboard connected
- [ ] ✅ Fallback controller ready
- [ ] ✅ Alert system configured
- [ ] ✅ Manual override accessible
- [ ] ✅ Team trained on system

### **First Day**:
- [ ] Run in **shadow mode** (agent decides, but don't execute)
- [ ] Compare agent decisions vs baseline
- [ ] Verify no safety violations

### **First Week**:
- [ ] Execute agent actions **with human supervision**
- [ ] Monitor performance closely
- [ ] Keep baseline controller ready to switch

### **After 1 Month**:
- [ ] Full autonomous operation
- [ ] Weekly performance reviews
- [ ] Monthly retraining evaluation

---

## 🎯 Summary

### **Key Insights**:

1. **No retraining needed for normal operation**
   - Model learned patterns, applies to new data
   - Like a trained driver handles new roads

2. **Real-time = Read sensors → Predict → Execute**
   - 15-minute cycle
   - No learning during execution
   - Safety checks always

3. **Retrain only when necessary**
   - Major changes (equipment, tariffs)
   - Significant performance drop
   - Not for normal weather variation

4. **Always have fallbacks**
   - Safety supervisor
   - Baseline controller
   - Manual override

### **What You Need to Build**:

**Minimum** (to demo):
- ✅ Load model
- ✅ Construct observation from data
- ✅ Get action
- ✅ Show on dashboard

**Production** (to deploy):
- ✅ All above +
- ✅ Sensor integration (SCADA/IoT)
- ✅ Safety supervisor
- ✅ Logging system
- ✅ Fallback controller
- ✅ Monitoring dashboard
- ✅ Alert system

---

## 🛠️ Complete Example: Simple Real-Time Simulator

```python
# deployment/simple_realtime.py

import torch
import numpy as np
import time
from datetime import datetime
from train_ppo_improved import ImprovedPPOAgent

# Load model
agent = ImprovedPPOAgent(obs_dim=90, action_dim=5)
agent.load("models/best_model.pt")

print("🚀 Simple Real-Time Simulator")
print("This simulates new data coming in every 5 seconds")
print("─" * 60)

step = 0

while True:
    # Simulate getting NEW sensor data
    # (In real deployment, replace with actual sensor readings)
    hour = (step % 96) * 0.25  # 0-24 hours
    solar = 2000 * np.sin(np.pi * hour / 12) if 6 <= hour <= 18 else 0
    wind = np.random.uniform(100, 500)
    load = 1000 + 500 * np.sin(np.pi * hour / 12)
    soc = 0.5 + 0.3 * np.sin(np.pi * step / 48)
    price = 3.0 if 6 <= hour <= 9 or 18 <= hour <= 21 else 2.0
    
    # Build observation (simplified, real one has 90 dims)
    obs = np.array([
        hour/24, solar/3000, wind/1000, load/2000, soc, price/10
    ] + [0]*84, dtype=np.float32)  # Pad to 90 dims
    
    # Agent decision
    action = agent.select_action(obs, deterministic=True)
    
    # Display
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] Step {step} (Hour {hour:.1f})")
    print(f"  Inputs:  Solar={solar:.0f}kW Wind={wind:.0f}kW Load={load:.0f}kW")
    print(f"  Battery: SoC={soc:.1%} Price=₹{price:.2f}/kWh")
    print(f"  AI Action: Battery1={action[0]:.0f}kW Battery2={action[1]:.0f}kW")
    print(f"            Grid={action[2]:.0f}kW EV={action[3]:.0f}kW")
    
    step += 1
    time.sleep(5)  # Wait 5 seconds (simulating 15 min)
```

**Run this**:
```bash
cd microgrid-ems-drl
python deployment/simple_realtime.py
```

---

**Ready to deploy? Let me know if you want me to create the complete deployment code!** 🚀
