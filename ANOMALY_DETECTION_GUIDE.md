# 🔍 Anomaly Detection & Predictive Maintenance Module

## Overview

This extensional module adds comprehensive **real-time anomaly detection** and **predictive maintenance** capabilities to the RL-based Energy Management System (EMS). It addresses Problem Statement 2 requirements by providing intelligent diagnostics, health monitoring, and actionable recommendations for all microgrid components.

## 🎯 Key Features

### 1. Real-Time Anomaly Detection
- **Statistical anomaly detection** using z-score analysis
- **Component-specific anomaly patterns**:
  - Battery: overcharge, deep discharge, over-temperature, rapid degradation
  - Solar PV: low performance, zero output during daylight, panel overheating
  - EV Chargers: low efficiency, frequent faults, connection issues
- **Confidence scoring** for each detected anomaly
- **Severity classification**: Info, Warning, Critical, Emergency

### 2. Predictive Maintenance
- **Time-to-failure estimation** based on degradation patterns
- **Maintenance type recommendations**: Inspection, Repair, Replacement, Calibration
- **Cost estimation** for maintenance activities (in INR)
- **Risk assessment** for ignored issues
- **Urgency prioritization** for scheduling

### 3. Health Monitoring
- **Component health indices** (0-100 scale):
  - Overall Health Score
  - Performance Index
  - Reliability Index
  - Degradation Rate
  - Estimated Remaining Life
- **Continuous tracking** of component status
- **Historical trend analysis**

### 4. Diagnostic Insights
- **Root cause analysis** for detected issues
- **Impact assessment** on system operations
- **Actionable recommendations** with specific steps
- **Priority ranking** for multiple issues

### 5. Alerting System
- **Real-time alerts** with severity levels
- **Recommended actions** for each alert
- **Alert history tracking**
- **Configurable thresholds**

## 📁 File Structure

```
microgrid-ems-drl/
├── anomaly_detection.py          # Core anomaly detection module
├── demo_anomaly_detection.py     # Demonstration script
├── cloud_api.py                  # Cloud dashboard API
├── dashboard.html                # Sample web dashboard
└── ANOMALY_DETECTION_GUIDE.md    # This file
```

## 🔧 Installation

### Required Dependencies

```bash
# Install core dependencies (if not already installed)
pip install numpy pandas
pip install gym

# For cloud API (optional)
pip install flask flask-cors flask-socketio
```

Add to `requirements.txt`:
```
flask>=2.0.0
flask-cors>=3.0.10
flask-socketio>=5.0.0
```

## 🚀 Quick Start

### 1. Basic Usage with Existing RL Environment

```python
from microgrid_env import MicrogridEMSEnv
from data_preprocessing import load_and_preprocess_data

# Load data
pv, wt, load, price = load_and_preprocess_data("data/synthetic_10year/COMPLETE_10YEAR_DATA.csv")

# Create environment (anomaly detection is automatically initialized)
env = MicrogridEMSEnv(
    pv_profile=pv,
    wt_profile=wt,
    load_profile=load,
    price_profile=price,
    enable_evs=True,
    enable_degradation=True
)

# Run simulation
obs = env.reset()
for step in range(96):  # 24 hours
    action = agent.act(obs)  # Your trained RL agent
    obs, reward, done, info = env.step(action)
    
    if done:
        break

# Get monitoring data
health_summary = env.get_system_health_summary()
health_indices = env.get_health_indices()
alerts = env.get_actionable_alerts()
report = env.get_anomaly_report()

# Display results
print(f"System Health: {health_summary['overall_health']:.1f}%")
print(f"Critical Alerts: {health_summary['critical_anomalies']}")

for alert in alerts:
    print(f"Alert: {alert['description']}")
    print(f"Action: {alert['recommended_action']}")
```

### 2. Run Demonstration

```bash
# Run comprehensive demonstration
python demo_anomaly_detection.py
```

This will:
- Show health monitoring for all components
- Demonstrate anomaly detection scenarios
- Display maintenance recommendations
- Generate a comprehensive JSON report

### 3. Start Cloud API & Dashboard

```bash
# Start the cloud API server
python cloud_api.py
```

Then open `dashboard.html` in your browser to see the real-time monitoring dashboard.

## 📊 Component Monitoring Details

### Battery Monitoring

**Tracked Metrics:**
- State of Charge (SoC) - 0-100%
- State of Health (SoH) - 0-100%
- Temperature - °C
- Cycles completed
- Total throughput - kWh

**Detected Anomalies:**
- Overcharge (SoC > 95%)
- Deep discharge (SoC < 15%)
- Over-temperature (> 45°C)
- Rapid degradation (SoH < 80%)

**Maintenance Triggers:**
- SoH < 80%: Replacement recommended
- Temperature events > 10: Cooling system inspection
- Deep discharge events > 15: BMS check

**Example Health Index:**
```python
{
    'component_id': 'Battery_5',
    'overall_health': 92.5,
    'performance_index': 94.0,
    'reliability_index': 91.0,
    'degradation_rate': 1.2,  # % per year
    'estimated_remaining_life': 61600.0  # hours (7 years)
}
```

### Solar PV Monitoring

**Tracked Metrics:**
- Power output - kW
- Performance ratio - %
- Solar irradiance - W/m²
- Panel temperature - °C

**Detected Anomalies:**
- Low performance (< 70% during high irradiance)
- Zero output during daylight
- Panel overheating (> 85°C)

**Maintenance Triggers:**
- Low performance count > 20: Cleaning/inspection
- Zero output: Emergency inspection
- Consistent underperformance: Inverter check

### EV Charger Monitoring

**Tracked Metrics:**
- Power output - kW
- Charging efficiency - %
- Temperature - °C
- Fault count

**Detected Anomalies:**
- Low efficiency (< 85%)
- Frequent faults (> 10)
- Overheating

**Maintenance Triggers:**
- Efficiency < 85%: Calibration
- Fault count > 10: Repair/replacement

## 🌐 Cloud API Integration

### REST API Endpoints

#### 1. System Status
```http
GET /api/system/status

Response:
{
    "timestamp": "2025-10-04T10:30:00",
    "health_summary": {
        "overall_health": 94.2,
        "components_monitored": 6,
        "critical_components": 0,
        "warning_components": 1
    },
    "total_alerts": 3,
    "critical_alerts": 0
}
```

#### 2. Component Health
```http
GET /api/components/health?component_id=Battery_5

Response:
{
    "component_id": "Battery_5",
    "data": {
        "overall_health": 92.5,
        "performance_index": 94.0,
        "reliability_index": 91.0,
        "degradation_rate": 1.2
    }
}
```

#### 3. Active Alerts
```http
GET /api/alerts/active

Response:
{
    "count": 2,
    "alerts": [
        {
            "timestamp": "2025-10-04T10:25:00",
            "component": "PV_System",
            "severity": "warning",
            "description": "PV system underperforming: 68.5%",
            "recommended_action": "Clean panels, check for shading"
        }
    ]
}
```

#### 4. Maintenance Recommendations
```http
GET /api/maintenance/recommendations

Response:
{
    "count": 1,
    "recommendations": [
        {
            "component": "Battery_5",
            "type": "inspection",
            "urgency": "warning",
            "description": "Battery experiencing overtemperature events",
            "action": "Inspect cooling system",
            "cost": 5000.0
        }
    ]
}
```

#### 5. IoT Data Ingestion
```http
POST /api/iot/ingest

Body:
{
    "component_id": "Battery_5",
    "timestamp": "2025-10-04T10:30:00",
    "measurements": {
        "soc": 75.0,
        "voltage": 52.4,
        "current": 120.0,
        "temperature": 35.2
    }
}

Response:
{
    "status": "success",
    "message": "Data ingested successfully"
}
```

### WebSocket Events

#### Subscribe to Updates
```javascript
const socket = io('http://localhost:5000');

socket.on('connect', () => {
    socket.emit('subscribe', { stream_type: 'all' });
});

// Receive health updates
socket.on('health_update', (data) => {
    console.log('Health update:', data.summary);
});

// Receive new alerts
socket.on('new_alerts', (data) => {
    console.log(`${data.count} new alerts:`, data.alerts);
});

// Receive IoT data
socket.on('iot_data', (data) => {
    console.log('IoT data:', data);
});
```

## 📈 Integration with RL Agent

The anomaly detection system is fully integrated with the RL environment:

```python
# In your training/evaluation loop
for episode in range(num_episodes):
    obs = env.reset()
    episode_done = False
    
    while not episode_done:
        # RL agent selects action
        action = agent.select_action(obs)
        
        # Execute action
        obs, reward, done, info = env.step(action)
        
        # Anomaly detection runs automatically in the background
        # Access monitoring data anytime:
        health = env.get_system_health_summary()
        
        # Check for critical alerts
        alerts = env.get_actionable_alerts()
        for alert in alerts:
            if alert['severity'] == 'critical':
                # Take emergency action
                print(f"CRITICAL: {alert['description']}")
                print(f"ACTION: {alert['recommended_action']}")
        
        episode_done = done
    
    # End-of-episode report
    report = env.get_anomaly_report()
    save_monitoring_report(report, episode)
```

## 🎯 Meeting Problem Statement Requirements

### ✅ Real-Time Monitoring
- [x] IoT data ingestion endpoints
- [x] Real-time component status tracking
- [x] Continuous health monitoring
- [x] Live dashboard updates via WebSocket

### ✅ Diagnostic Insights
- [x] Clear diagnostic outputs (not just anomaly flags)
- [x] Root cause identification
- [x] Impact assessment
- [x] Actionable recommendations

### ✅ Health Indices
- [x] Battery health index
- [x] Solar PV performance index
- [x] EV charger health tracking
- [x] System-wide health summary

### ✅ Real-Time Alerts
- [x] Critical issue detection
- [x] Severity classification
- [x] Recommended actions included
- [x] Alert history tracking

### ✅ RL Integration
- [x] Compatible with existing RL agent
- [x] Advisory suggestions from RL
- [x] Energy dispatch optimization
- [x] Cost & emissions minimization

### ✅ Cloud Dashboard
- [x] REST API for data access
- [x] WebSocket for real-time updates
- [x] Component status visualization
- [x] Alert management
- [x] Maintenance scheduling

## 📊 Example Outputs

### Health Summary
```
Overall System Health: 94.2%
Components Monitored: 6
Critical Components: 0
Warning Components: 1
Total Anomalies: 15
Critical Anomalies: 2
```

### Component Health
```
✅ Battery_5 (BATTERY)
   Overall Health: 92.5%
   Performance Index: 94.0%
   Reliability Index: 91.0%
   Degradation Rate: 1.2% per year
   Est. Remaining Life: 61600 hours (7.0 years)

⚠️  PV_System (SOLAR_PV)
   Overall Health: 75.3%
   Performance Index: 75.3%
   Low performance events detected
```

### Alerts
```
🔴 Alert - CRITICAL
   Component: PV_System
   Type: zero_output
   Description: PV system producing no power during daylight hours
   ➜ Action: Immediate inspection - check inverter, wiring, and panel connections
```

### Maintenance Recommendations
```
🔧 Recommendation - WARNING
   Component: Battery_5
   Type: inspection
   Description: Battery experiencing frequent overtemperature events
   ➜ Action: Inspect cooling system, check thermal management
   Estimated Cost: ₹5,000
   Risk if ignored: Accelerated degradation, reduced lifespan, fire risk
```

## 🔄 Continuous Improvement

### Future Enhancements

1. **Machine Learning-Based Anomaly Detection**
   - Train ML models on historical data
   - Detect complex multi-variate anomalies
   - Improve prediction accuracy

2. **Advanced Predictive Analytics**
   - Remaining Useful Life (RUL) prediction
   - Failure mode analysis
   - Optimal maintenance scheduling

3. **Integration with External Systems**
   - SCADA integration
   - Weather API for solar forecasting
   - Grid operator communications

4. **Enhanced Visualization**
   - 3D system topology
   - Interactive trend charts
   - Predictive analytics dashboards

## 📚 References

- VidyutAI Hackathon 2025 Problem Statement 2
- IEEE Standards for Energy Management Systems
- IEC 61850 for Power System Communication
- Indian Grid Code and Standards

## 🤝 Support

For issues or questions:
1. Check the demonstration script: `demo_anomaly_detection.py`
2. Review API documentation in `cloud_api.py`
3. Examine example outputs in generated reports

## 📄 License

This module is part of the Microgrid EMS project and follows the same license.

---

**Built for VidyutAI Hackathon 2025 - Problem Statement 2**
*Next-Gen EMS with Real-Time Monitoring & Predictive Maintenance*
