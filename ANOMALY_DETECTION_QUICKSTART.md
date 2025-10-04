# 🚀 Quick Start: Anomaly Detection & Predictive Maintenance Module

## What's New? 🎉

Your RL-based Energy Management System now includes a comprehensive **Anomaly Detection and Predictive Maintenance** module that provides:

- **Real-time health monitoring** for all microgrid components
- **Intelligent anomaly detection** with confidence scoring
- **Predictive maintenance recommendations** with cost estimates
- **Actionable alerts** with specific remediation steps
- **Cloud-ready API** for dashboard integration
- **WebSocket support** for real-time data streaming

## 🎯 Meets All Problem Statement 2 Requirements

✅ **Real-Time Monitoring**: IoT data ingestion, continuous tracking  
✅ **Diagnostic Insights**: Root cause analysis, not just anomaly flags  
✅ **Health Indices**: Per-component and system-wide health scores  
✅ **Real-Time Alerts**: With recommended actions  
✅ **RL Integration**: Works seamlessly with existing RL agent  
✅ **Cloud Dashboard**: REST API + WebSocket for visualization  

## 📦 Installation

### 1. Basic Installation (Core Features)
```bash
# Already installed if you have the main project
# No additional dependencies needed!
```

### 2. Optional: Cloud API & Dashboard
```bash
pip install flask flask-cors flask-socketio python-socketio
```

## 🏃 Quick Start Guide

### Option 1: Run Demonstration (Recommended First Step)

```bash
cd microgrid-ems-drl
python demo_anomaly_detection.py
```

This will:
- ✓ Show health monitoring for batteries, solar PV, and EV chargers
- ✓ Demonstrate anomaly detection scenarios
- ✓ Display maintenance recommendations with cost estimates
- ✓ Generate a comprehensive JSON monitoring report
- ✓ Test various fault scenarios

**Expected Output:**
```
🔍 Anomaly Detection & Predictive Maintenance System Demonstration
================================================================================

📊 Loading microgrid data...
✓ Data loaded: 87600 timesteps

🏗️  Creating microgrid environment with anomaly detection...
✓ Environment initialized with anomaly detection system

📈 SYSTEM HEALTH SUMMARY
Overall System Health: 94.2%
Components Monitored: 6
Critical Components: 0
Warning Components: 1

🔋 COMPONENT HEALTH INDICES
✅ Battery_5 (BATTERY)
   Overall Health: 92.5%
   Performance Index: 94.0%
   ...
```

### Option 2: Integrate with Your Existing Code

```python
from microgrid_env import MicrogridEMSEnv
from data_preprocessing import load_and_preprocess_data

# Load your data
pv, wt, load, price = load_and_preprocess_data("data/synthetic_10year/COMPLETE_10YEAR_DATA.csv")

# Create environment (anomaly detection auto-initialized!)
env = MicrogridEMSEnv(
    pv_profile=pv,
    wt_profile=wt,
    load_profile=load,
    price_profile=price,
    enable_evs=True,
    enable_degradation=True
)

# Run your RL agent as normal
obs = env.reset()
for step in range(96):  # 24 hours
    action = agent.act(obs)  # Your trained agent
    obs, reward, done, info = env.step(action)
    
    # NEW: Access monitoring data anytime
    health = env.get_system_health_summary()
    alerts = env.get_actionable_alerts()
    
    # Check for critical issues
    for alert in alerts:
        if alert['severity'] == 'critical':
            print(f"⚠️  {alert['description']}")
            print(f"➜ {alert['recommended_action']}")
    
    if done:
        break

# Get comprehensive report
report = env.get_anomaly_report()
print(f"System Health: {report['system_summary']['overall_health']:.1f}%")
```

### Option 3: Start Cloud API & Dashboard

```bash
# Terminal 1: Start API server
python cloud_api.py

# Terminal 2: Open dashboard
# Open dashboard.html in your browser
# Navigate to: http://localhost:5000
```

The dashboard provides:
- Real-time system health visualization
- Component status monitoring
- Active alerts display
- Maintenance recommendations
- Historical trend analysis

## 📊 What You Can Monitor

### 1. Battery Systems
- **Metrics**: SoC, SoH, Temperature, Cycles, Throughput
- **Anomalies**: Overcharge, Deep discharge, Over-temperature, Rapid degradation
- **Maintenance**: Replacement timing, Cooling system checks, BMS diagnostics

### 2. Solar PV Systems
- **Metrics**: Power output, Performance ratio, Irradiance, Panel temperature
- **Anomalies**: Low performance, Zero output, Overheating
- **Maintenance**: Panel cleaning, Inverter inspection, Connection checks

### 3. EV Chargers
- **Metrics**: Power output, Efficiency, Temperature, Fault count
- **Anomalies**: Low efficiency, Frequent faults
- **Maintenance**: Calibration, Repair, Replacement

### 4. System-Wide
- **Overall health score** (0-100%)
- **Component count** and status
- **Active alerts** with severity
- **Maintenance recommendations** with costs

## 🎯 Use Cases

### Use Case 1: Daily Operations
```python
# Morning system check
health_summary = env.get_system_health_summary()
if health_summary['critical_components'] > 0:
    alerts = env.get_actionable_alerts()
    # Send notifications to operators
```

### Use Case 2: Maintenance Planning
```python
# Weekly maintenance review
report = env.get_anomaly_report()
recommendations = report['maintenance_recommendations']

for rec in recommendations:
    if rec['urgency'] == 'critical':
        # Schedule immediate maintenance
        schedule_maintenance(rec['component'], rec['action'])
```

### Use Case 3: Real-Time Dashboard
```python
from cloud_api import CloudEMSAPI

api = CloudEMSAPI(host='0.0.0.0', port=5000)

# Connect to environment
# Start background monitoring
api.start_background_monitoring(env)

# Run API server
api.run()
```

### Use Case 4: IoT Integration
```bash
# Send IoT sensor data
curl -X POST http://localhost:5000/api/iot/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "component_id": "Battery_5",
    "timestamp": "2025-10-04T10:30:00",
    "measurements": {
      "soc": 75.0,
      "voltage": 52.4,
      "current": 120.0,
      "temperature": 35.2
    }
  }'
```

## 📈 Example Outputs

### Health Summary
```json
{
  "overall_health": 94.2,
  "components_monitored": 6,
  "critical_components": 0,
  "warning_components": 1,
  "total_anomalies": 15,
  "critical_anomalies": 2
}
```

### Alert Example
```json
{
  "severity": "warning",
  "component": "PV_System",
  "type": "low_performance",
  "description": "PV system underperforming: 68.5% (expected >75%)",
  "recommended_action": "Clean panels, check for shading, inspect inverter connections"
}
```

### Maintenance Recommendation
```json
{
  "component": "Battery_5",
  "type": "inspection",
  "urgency": "warning",
  "description": "Battery experiencing frequent overtemperature events",
  "action": "Inspect cooling system, check thermal management",
  "cost": 5000.0,
  "risk_if_ignored": "Accelerated degradation, reduced lifespan, fire risk"
}
```

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system/status` | GET | Overall system health |
| `/api/components/health` | GET | Component health indices |
| `/api/alerts` | GET | All alerts (paginated) |
| `/api/alerts/active` | GET | Currently active alerts |
| `/api/maintenance/recommendations` | GET | Maintenance recommendations |
| `/api/diagnostics` | GET | Diagnostic insights |
| `/api/iot/ingest` | POST | Ingest IoT sensor data |

## 📝 Generated Reports

After running the demonstration or your simulation, you'll get:

1. **Console Output**: Real-time health summary and alerts
2. **JSON Report**: `monitoring_report_YYYYMMDD_HHMMSS.json`
   - Complete system state
   - All component health indices
   - Active alerts
   - Maintenance recommendations
   - Diagnostic insights

Example report structure:
```json
{
  "timestamp": "2025-10-04T10:30:00",
  "system_summary": {...},
  "health_indices": {...},
  "active_alerts": [...],
  "maintenance_recommendations": [...],
  "diagnostic_insights": [...]
}
```

## 🔄 Integration with RL Training

The anomaly detection runs automatically during RL training:

```python
# In your training loop
for episode in range(num_episodes):
    obs = env.reset()
    
    while not done:
        action = agent.select_action(obs)
        obs, reward, done, info = env.step(action)
        
        # Anomaly detection happens automatically!
        # Access monitoring data:
        if step % 96 == 0:  # Check every 24 hours
            health = env.get_system_health_summary()
            print(f"System Health: {health['overall_health']:.1f}%")
    
    # End-of-episode report
    report = env.get_anomaly_report()
    save_report(report, episode)
```

## 🎓 Learn More

- **Full Documentation**: `ANOMALY_DETECTION_GUIDE.md`
- **Core Module**: `anomaly_detection.py`
- **Demo Script**: `demo_anomaly_detection.py`
- **Cloud API**: `cloud_api.py`
- **Dashboard**: `dashboard.html`

## 🛠️ Troubleshooting

### Issue: "Module not found: anomaly_detection"
**Solution**: Make sure you're in the `microgrid-ems-drl` directory

### Issue: "Flask not found"
**Solution**: Install cloud API dependencies:
```bash
pip install flask flask-cors flask-socketio
```

### Issue: "No data files found"
**Solution**: The demo works with or without data. If you see warnings, it will use sample data.

### Issue: WebSocket connection fails
**Solution**: 
1. Check if API server is running (`python cloud_api.py`)
2. Verify port 5000 is not blocked
3. Try accessing http://localhost:5000 first

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] Run `python demo_anomaly_detection.py` successfully
- [ ] See health monitoring output
- [ ] Get anomaly detection results
- [ ] Receive maintenance recommendations
- [ ] Generate JSON report
- [ ] (Optional) Start cloud API
- [ ] (Optional) Access dashboard

## 🎉 Success!

You now have a complete anomaly detection and predictive maintenance system integrated with your RL-based EMS!

**Next Steps:**
1. Run the demonstration to see it in action
2. Integrate with your existing code
3. (Optional) Set up the cloud dashboard
4. Customize thresholds and parameters for your use case
5. Deploy to production with your trained RL agent

## 📞 Need Help?

- Check the full guide: `ANOMALY_DETECTION_GUIDE.md`
- Review example code: `demo_anomaly_detection.py`
- Examine the module: `anomaly_detection.py`

---

**🏆 Built for VidyutAI Hackathon 2025 - Problem Statement 2**

*Complete solution for Next-Gen EMS with Real-Time Monitoring, Intelligent Diagnostics, and Adaptive Decision-Making*
