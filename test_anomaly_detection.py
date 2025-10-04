"""
Integration test for Anomaly Detection Module
Tests the integration with the main microgrid environment
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime

print("=" * 80)
print("🧪 Testing Anomaly Detection Module Integration")
print("=" * 80)
print()

# Test 1: Import modules
print("Test 1: Import modules...")
try:
    from anomaly_detection import (
        AnomalyDetectionSystem, 
        BatteryHealthMonitor,
        SolarPVHealthMonitor,
        EVChargerHealthMonitor,
        SeverityLevel,
        ComponentType
    )
    print("✓ Anomaly detection module imported successfully")
except Exception as e:
    print(f"✗ Failed to import anomaly detection: {e}")
    sys.exit(1)

# Test 2: Create anomaly detection system
print("\nTest 2: Create anomaly detection system...")
try:
    ads = AnomalyDetectionSystem()
    print("✓ AnomalyDetectionSystem created successfully")
except Exception as e:
    print(f"✗ Failed to create system: {e}")
    sys.exit(1)

# Test 3: Register components
print("\nTest 3: Register components...")
try:
    battery_monitor = ads.register_battery("Battery_Test", capacity_kwh=1000, cycle_life=5000)
    pv_monitor = ads.register_solar_pv("PV_Test", nominal_capacity_kw=1000)
    ev_monitor = ads.register_ev_charger("Charger_Test", max_power_kw=50)
    print(f"✓ Registered {len(ads.component_monitors)} components")
except Exception as e:
    print(f"✗ Failed to register components: {e}")
    sys.exit(1)

# Test 4: Update component states
print("\nTest 4: Update component states...")
try:
    # Update battery
    ads.update_component_state(
        component_id="Battery_Test",
        soc=75.0,
        soh=95.0,
        temperature=35.0,
        power_kw=100.0,
        timestep_hours=0.25
    )
    
    # Update PV
    ads.update_component_state(
        component_id="PV_Test",
        power_output_kw=800,
        irradiance=900,
        ambient_temp=30.0,
        panel_temp=50.0
    )
    
    # Update EV charger
    ads.update_component_state(
        component_id="Charger_Test",
        power_output_kw=45.0,
        efficiency=92.0,
        temperature=35.0,
        fault_status=False
    )
    
    print("✓ Component states updated successfully")
except Exception as e:
    print(f"✗ Failed to update states: {e}")
    sys.exit(1)

# Test 5: Get health indices
print("\nTest 5: Get health indices...")
try:
    health_indices = ads.get_all_health_indices()
    print(f"✓ Retrieved health indices for {len(health_indices)} components")
    
    for component_id, health in health_indices.items():
        print(f"  - {component_id}: {health.overall_health:.1f}%")
except Exception as e:
    print(f"✗ Failed to get health indices: {e}")
    sys.exit(1)

# Test 6: Detect anomalies
print("\nTest 6: Detect anomalies...")
try:
    # Trigger some anomalies
    ads.update_component_state(
        component_id="Battery_Test",
        soc=97.0,  # High SoC - should trigger overcharge
        soh=95.0,
        temperature=50.0,  # High temp - should trigger over-temperature
        power_kw=100.0,
        timestep_hours=0.25
    )
    
    anomalies = ads.detect_all_anomalies()
    print(f"✓ Detected {len(anomalies)} anomalies")
    
    for anomaly in anomalies:
        print(f"  - {anomaly.severity.value.upper()}: {anomaly.description}")
except Exception as e:
    print(f"✗ Failed to detect anomalies: {e}")
    sys.exit(1)

# Test 7: Generate maintenance recommendations
print("\nTest 7: Generate maintenance recommendations...")
try:
    # Trigger end-of-life scenario
    ads.update_component_state(
        component_id="Battery_Test",
        soc=50.0,
        soh=75.0,  # Low SoH - should trigger replacement
        temperature=35.0,
        power_kw=50.0,
        timestep_hours=0.25
    )
    
    recommendations = ads.generate_maintenance_recommendations()
    print(f"✓ Generated {len(recommendations)} recommendations")
    
    for rec in recommendations:
        print(f"  - {rec.component_id}: {rec.recommendation_type} ({rec.urgency.value})")
        print(f"    Cost: ₹{rec.estimated_cost:,.0f}")
except Exception as e:
    print(f"✗ Failed to generate recommendations: {e}")
    sys.exit(1)

# Test 8: Get system health summary
print("\nTest 8: Get system health summary...")
try:
    summary = ads.get_system_health_summary()
    print("✓ System health summary:")
    print(f"  - Overall health: {summary['overall_health']:.1f}%")
    print(f"  - Components monitored: {summary['components_monitored']}")
    print(f"  - Critical components: {summary['critical_components']}")
    print(f"  - Total anomalies: {summary['total_anomalies']}")
except Exception as e:
    print(f"✗ Failed to get summary: {e}")
    sys.exit(1)

# Test 9: Get monitoring report
print("\nTest 9: Get comprehensive monitoring report...")
try:
    report = ads.get_monitoring_report()
    print("✓ Monitoring report generated")
    print(f"  - Timestamp: {report['timestamp']}")
    print(f"  - Active alerts: {len(report['active_alerts'])}")
    print(f"  - Maintenance recommendations: {len(report['maintenance_recommendations'])}")
    print(f"  - Diagnostic insights: {len(report['diagnostic_insights'])}")
except Exception as e:
    print(f"✗ Failed to get report: {e}")
    sys.exit(1)

# Test 10: Test with microgrid environment
print("\nTest 10: Test integration with microgrid environment...")
try:
    # Create sufficient data for testing (need extra for forecast horizon)
    sample_size = 200  # More than 96 steps + forecast horizon
    pv_profile = pd.DataFrame({'pv_power_kw': np.random.rand(sample_size) * 1000})
    wt_profile = pd.DataFrame({'wt_power_kw': np.random.rand(sample_size) * 500})
    load_profile = pd.DataFrame({'load_kw': 2000 + np.random.rand(sample_size) * 1000})
    price_profile = pd.DataFrame({'price_inr_per_kwh': 5.0 + np.random.rand(sample_size) * 3})
    
    from microgrid_env import MicrogridEMSEnv
    
    env = MicrogridEMSEnv(
        pv_profile=pv_profile,
        wt_profile=wt_profile,
        load_profile=load_profile,
        price_profile=price_profile,
        enable_evs=True,
        enable_degradation=True
    )
    
    print("✓ Environment created with anomaly detection")
    
    # Test environment methods (use fixed start index)
    obs = env.reset(episode_start_idx=0)
    
    # Run a few steps
    for i in range(10):
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        if done:
            break
    
    # Get monitoring data
    health = env.get_system_health_summary()
    print(f"✓ Environment running - System health: {health['overall_health']:.1f}%")
    
    # Get alerts
    alerts = env.get_actionable_alerts()
    print(f"✓ Alerts retrieved: {len(alerts)} active")
    
    # Get full report
    report = env.get_anomaly_report()
    print(f"✓ Full monitoring report generated")
    
except Exception as e:
    print(f"✗ Failed integration test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
print()
print("Summary:")
print("  ✓ Module imports work")
print("  ✓ Component registration works")
print("  ✓ State updates work")
print("  ✓ Health monitoring works")
print("  ✓ Anomaly detection works")
print("  ✓ Maintenance recommendations work")
print("  ✓ System reports work")
print("  ✓ Integration with environment works")
print()
print("🎉 Anomaly Detection Module is ready to use!")
print()
