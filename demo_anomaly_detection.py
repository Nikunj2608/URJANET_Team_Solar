"""
Demonstration script for Anomaly Detection and Predictive Maintenance System
Shows integration with RL-based EMS and real-time monitoring capabilities
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

from microgrid_env import MicrogridEMSEnv
from anomaly_detection import AnomalyDetectionSystem, SeverityLevel


def load_data_profiles():
    """Load pre-processed data profiles or use synthetic data"""
    data_dir = Path("data")
    
    # Try to load pre-processed data
    pv_file = data_dir / "pv_profile_processed.csv"
    wt_file = data_dir / "wt_profile_processed.csv"
    load_file = data_dir / "load_profile_processed.csv"
    price_file = data_dir / "price_profile_processed.csv"
    
    if all(f.exists() for f in [pv_file, wt_file, load_file, price_file]):
        print("Loading pre-processed data profiles...")
        pv_profile = pd.read_csv(pv_file)
        wt_profile = pd.read_csv(wt_file)
        load_profile = pd.read_csv(load_file)
        price_profile = pd.read_csv(price_file)
        return pv_profile, wt_profile, load_profile, price_profile
    
    # Try to load 10-year synthetic data
    synthetic_file = data_dir / "synthetic_10year" / "COMPLETE_10YEAR_DATA.csv"
    if synthetic_file.exists():
        print("Loading 10-year synthetic data...")
        df = pd.read_csv(synthetic_file)
        
        # Extract profiles
        pv_profile = pd.DataFrame({'pv_power_kw': df['pv_power_kw']})
        wt_profile = pd.DataFrame({'wt_power_kw': df['wt_power_kw']})
        load_profile = pd.DataFrame({'load_kw': df['load_kw']})
        price_profile = pd.DataFrame({'price_inr_per_kwh': df['price_inr_per_kwh']})
        
        return pv_profile, wt_profile, load_profile, price_profile
    
    # Fall back to creating minimal synthetic data
    print("⚠ No data files found. Creating minimal synthetic data for demo...")
    return None, None, None, None


def demonstrate_anomaly_detection():
    """Demonstrate the anomaly detection system with a simple scenario"""
    
    print("=" * 80)
    print("🔍 Anomaly Detection & Predictive Maintenance System Demonstration")
    print("=" * 80)
    print()
    
    # Load data
    print("📊 Loading microgrid data...")
    
    pv_profile, wt_profile, load_profile, price_profile = load_data_profiles()
    
    if pv_profile is None:
        # Create minimal sample data for demonstration
        print("⚠ Creating sample data for demonstration...")
        sample_size = 96 * 30  # 30 days
        pv_profile = pd.DataFrame({'pv_power_kw': np.random.rand(sample_size) * 1000})
        wt_profile = pd.DataFrame({'wt_power_kw': np.random.rand(sample_size) * 500})
        load_profile = pd.DataFrame({'load_kw': 2000 + np.random.rand(sample_size) * 1000})
        price_profile = pd.DataFrame({'price_inr_per_kwh': 5.0 + np.random.rand(sample_size) * 3})
    
    print(f"✓ Data loaded: {len(pv_profile)} timesteps")
    
    print()
    
    # Create environment with anomaly detection
    print("🏗️  Creating microgrid environment with anomaly detection...")
    env = MicrogridEMSEnv(
        pv_profile=pv_profile,
        wt_profile=wt_profile,
        load_profile=load_profile,
        price_profile=price_profile,
        enable_evs=True,
        enable_degradation=True,
        enable_emissions=True
    )
    print("✓ Environment initialized with anomaly detection system")
    print()
    
    # Run simulation
    print("🔄 Running simulation to collect monitoring data...")
    obs = env.reset()
    
    total_steps = 96  # Run for 24 hours (96 x 15-minute intervals)
    anomalies_detected = []
    
    for step in range(total_steps):
        # Random action for demonstration (replace with trained RL agent)
        action = env.action_space.sample()
        
        obs, reward, done, info = env.step(action)
        
        if done:
            break
    
    print(f"✓ Simulation completed: {step + 1} timesteps")
    print()
    
    # Get health summary
    print("=" * 80)
    print("📈 SYSTEM HEALTH SUMMARY")
    print("=" * 80)
    health_summary = env.get_system_health_summary()
    
    print(f"Overall System Health: {health_summary['overall_health']:.1f}%")
    print(f"Components Monitored: {health_summary['components_monitored']}")
    print(f"Critical Components: {health_summary['critical_components']}")
    print(f"Warning Components: {health_summary['warning_components']}")
    print(f"Total Anomalies Detected: {health_summary['total_anomalies']}")
    print(f"Critical Anomalies: {health_summary['critical_anomalies']}")
    print(f"Active Recommendations: {health_summary['active_recommendations']}")
    print()
    
    # Get detailed health indices
    print("=" * 80)
    print("🔋 COMPONENT HEALTH INDICES")
    print("=" * 80)
    health_indices = env.get_health_indices()
    
    for component_id, health in health_indices.items():
        status_emoji = "✅" if health.overall_health >= 85 else "⚠️" if health.overall_health >= 70 else "🔴"
        print(f"\n{status_emoji} {component_id} ({health.component_type.value.upper()})")
        print(f"   Overall Health: {health.overall_health:.1f}%")
        print(f"   Performance Index: {health.performance_index:.1f}%")
        print(f"   Reliability Index: {health.reliability_index:.1f}%")
        print(f"   Degradation Rate: {health.degradation_rate:.2f}% per year")
        if health.estimated_remaining_life < float('inf'):
            print(f"   Est. Remaining Life: {health.estimated_remaining_life:.0f} hours ({health.estimated_remaining_life/8760:.1f} years)")
    
    print()
    
    # Get actionable alerts
    print("=" * 80)
    print("🚨 ACTIONABLE ALERTS & RECOMMENDATIONS")
    print("=" * 80)
    alerts = env.get_actionable_alerts()
    
    if alerts:
        for i, alert in enumerate(alerts[-10:], 1):  # Show last 10 alerts
            severity_emoji = {
                'critical': '🔴',
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(alert['severity'], '•')
            
            print(f"\n{severity_emoji} Alert #{i} - {alert['severity'].upper()}")
            print(f"   Component: {alert['component']}")
            print(f"   Type: {alert['type']}")
            print(f"   Description: {alert['description']}")
            print(f"   ➜ Action: {alert['recommended_action']}")
    else:
        print("✓ No active alerts - all systems operating normally")
    
    print()
    
    # Get comprehensive monitoring report
    print("=" * 80)
    print("📋 COMPREHENSIVE MONITORING REPORT")
    print("=" * 80)
    report = env.get_anomaly_report()
    
    # Save report to JSON
    report_file = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        # Convert health indices to serializable format
        serializable_report = {
            'timestamp': report['timestamp'],
            'system_summary': report['system_summary'],
            'health_indices': report['health_indices'],
            'active_alerts': report['active_alerts'],
            'maintenance_recommendations': report['maintenance_recommendations'],
            'diagnostic_insights': report['diagnostic_insights']
        }
        json.dump(serializable_report, f, indent=2, default=str)
    
    print(f"✓ Full monitoring report saved to: {report_file}")
    print()
    
    # Display maintenance recommendations
    if report['maintenance_recommendations']:
        print("=" * 80)
        print("🔧 PREDICTIVE MAINTENANCE RECOMMENDATIONS")
        print("=" * 80)
        
        for i, rec in enumerate(report['maintenance_recommendations'], 1):
            urgency_emoji = {
                'critical': '🔴',
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(rec['urgency'], '•')
            
            print(f"\n{urgency_emoji} Recommendation #{i} - {rec['urgency'].upper()}")
            print(f"   Component: {rec['component']}")
            print(f"   Type: {rec['type'].title()}")
            print(f"   Description: {rec['description']}")
            print(f"   ➜ Action: {rec['action']}")
            print(f"   Estimated Cost: ₹{rec['cost']:,.0f}")
    else:
        print("✓ No maintenance required at this time")
    
    print()
    
    # Display diagnostic insights
    if report['diagnostic_insights']:
        print("=" * 80)
        print("🔬 DIAGNOSTIC INSIGHTS")
        print("=" * 80)
        
        for i, insight in enumerate(report['diagnostic_insights'], 1):
            print(f"\n{i}. {insight['component']} ({insight['component_type'].upper()})")
            print(f"   Issue: {insight['issue']}")
            print(f"   Root Cause: {insight['root_cause']}")
            print(f"   Impact: {insight['impact']}")
            print(f"   ➜ Recommended Action: {insight['action']}")
            print(f"   Priority: {insight['priority']}/5")
    
    print()
    print("=" * 80)
    print("✅ Demonstration Complete!")
    print("=" * 80)
    print()
    print("Key Features Demonstrated:")
    print("  • Real-time component health monitoring")
    print("  • Anomaly detection using statistical methods")
    print("  • Predictive maintenance recommendations")
    print("  • Actionable alerts with specific remediation steps")
    print("  • Diagnostic insights with root cause analysis")
    print("  • Integration with RL-based energy management")
    print()


def simulate_anomaly_scenarios():
    """Simulate specific anomaly scenarios for testing"""
    
    print("=" * 80)
    print("🧪 ANOMALY SCENARIO TESTING")
    print("=" * 80)
    print()
    
    # Create standalone anomaly detection system
    ads = AnomalyDetectionSystem()
    
    # Register components
    battery_monitor = ads.register_battery("Battery_Test", capacity_kwh=1000, cycle_life=5000)
    pv_monitor = ads.register_solar_pv("PV_Test", nominal_capacity_kw=1000)
    
    print("Testing various anomaly scenarios...\n")
    
    # Scenario 1: Battery overcharge
    print("📍 Scenario 1: Battery Overcharge")
    ads.update_component_state(
        component_id="Battery_Test",
        soc=97.0,  # High SoC
        soh=95.0,
        temperature=35.0,
        power_kw=100.0,
        timestep_hours=0.25
    )
    anomalies = battery_monitor.detect_battery_anomalies()
    if anomalies:
        for a in anomalies:
            print(f"   ⚠️  {a.severity.value.upper()}: {a.description}")
    else:
        print("   ✓ No anomalies detected")
    print()
    
    # Scenario 2: Battery overheating
    print("📍 Scenario 2: Battery Overheating")
    ads.update_component_state(
        component_id="Battery_Test",
        soc=60.0,
        soh=95.0,
        temperature=52.0,  # High temperature
        power_kw=200.0,
        timestep_hours=0.25
    )
    anomalies = battery_monitor.detect_battery_anomalies()
    if anomalies:
        for a in anomalies:
            print(f"   🔴 {a.severity.value.upper()}: {a.description}")
    else:
        print("   ✓ No anomalies detected")
    print()
    
    # Scenario 3: Battery end of life
    print("📍 Scenario 3: Battery End of Life")
    ads.update_component_state(
        component_id="Battery_Test",
        soc=50.0,
        soh=75.0,  # Low SoH
        temperature=35.0,
        power_kw=50.0,
        timestep_hours=0.25
    )
    anomalies = battery_monitor.detect_battery_anomalies()
    if anomalies:
        for a in anomalies:
            print(f"   🔴 {a.severity.value.upper()}: {a.description}")
    
    maintenance = battery_monitor.get_maintenance_recommendation()
    if maintenance:
        print(f"   🔧 Maintenance Required: {maintenance.recommendation_type}")
        print(f"   Action: {maintenance.recommended_action}")
        print(f"   Estimated Cost: ₹{maintenance.estimated_cost:,.0f}")
    print()
    
    # Scenario 4: PV underperformance
    print("📍 Scenario 4: Solar PV Underperformance")
    for _ in range(25):  # Trigger persistent low performance
        ads.update_component_state(
            component_id="PV_Test",
            power_output_kw=400,  # Low output
            irradiance=800,  # High irradiance
            ambient_temp=30.0,
            panel_temp=55.0
        )
    
    anomalies = pv_monitor.detect_pv_anomalies()
    if anomalies:
        for a in anomalies:
            print(f"   ⚠️  {a.severity.value.upper()}: {a.description}")
    
    maintenance = pv_monitor.get_maintenance_recommendation()
    if maintenance:
        print(f"   🔧 Maintenance Required: {maintenance.recommendation_type}")
        print(f"   Action: {maintenance.recommended_action}")
        print(f"   Estimated Cost: ₹{maintenance.estimated_cost:,.0f}")
    print()
    
    print("=" * 80)
    print("✅ Anomaly Scenario Testing Complete!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    # Run main demonstration
    demonstrate_anomaly_detection()
    
    print("\n" + "=" * 80 + "\n")
    
    # Run scenario testing
    simulate_anomaly_scenarios()
    
    print("\n" + "=" * 80)
    print("💡 Integration Guide:")
    print("=" * 80)
    print("""
The anomaly detection system is now integrated with the RL-based EMS.

To use it in your application:

1. Access real-time health data:
   health_summary = env.get_system_health_summary()
   health_indices = env.get_health_indices()

2. Get actionable alerts:
   alerts = env.get_actionable_alerts()
   for alert in alerts:
       print(f"Alert: {alert['description']}")
       print(f"Action: {alert['recommended_action']}")

3. Get maintenance recommendations:
   report = env.get_anomaly_report()
   recommendations = report['maintenance_recommendations']

4. Build dashboard integration:
   - Use get_anomaly_report() to get comprehensive JSON data
   - Stream to cloud dashboard (Azure IoT Hub, AWS IoT, etc.)
   - Display in real-time web interface
   - Set up automated alerting

5. API Integration:
   - Create REST API endpoints for monitoring data
   - Implement WebSocket for real-time updates
   - Use MQTT for IoT device communication

See the generated JSON report for full data structure.
    """)
