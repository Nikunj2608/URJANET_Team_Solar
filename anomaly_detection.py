"""
Anomaly Detection and Predictive Maintenance Module
Provides real-time anomaly detection, health monitoring, and maintenance recommendations
for microgrid components: Solar PV, Wind Turbines, Batteries, Inverters, EV Chargers, and Grid

Features:
- Real-time anomaly detection using statistical methods and ML
- Component health indices calculation
- Predictive maintenance scheduling
- Diagnostic insights and actionable recommendations
- Integration with existing RL-based EMS
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum


class SeverityLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ComponentType(Enum):
    """Types of microgrid components"""
    BATTERY = "battery"
    SOLAR_PV = "solar_pv"
    WIND_TURBINE = "wind_turbine"
    INVERTER = "inverter"
    EV_CHARGER = "ev_charger"
    GRID_CONNECTION = "grid_connection"
    TRANSFORMER = "transformer"


@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    timestamp: datetime
    component_id: str
    component_type: ComponentType
    anomaly_type: str
    severity: SeverityLevel
    description: str
    current_value: float
    expected_value: float
    deviation: float
    confidence: float  # 0-1
    
    
@dataclass
class MaintenanceRecommendation:
    """Predictive maintenance recommendation"""
    component_id: str
    component_type: ComponentType
    recommendation_type: str  # 'inspection', 'repair', 'replacement', 'calibration'
    urgency: SeverityLevel
    description: str
    estimated_time_to_failure: Optional[float]  # hours
    recommended_action: str
    estimated_downtime: float  # hours
    estimated_cost: float  # INR
    risk_if_ignored: str
    
    
@dataclass
class HealthIndex:
    """Component health index"""
    component_id: str
    component_type: ComponentType
    overall_health: float  # 0-100
    performance_index: float  # 0-100
    reliability_index: float  # 0-100
    degradation_rate: float  # % per year
    estimated_remaining_life: float  # hours
    last_maintenance: Optional[datetime]
    next_maintenance_due: Optional[datetime]
    
    
@dataclass
class DiagnosticInsight:
    """Detailed diagnostic information"""
    component_id: str
    component_type: ComponentType
    issue: str
    root_cause: str
    impact: str
    recommended_action: str
    priority: int  # 1-5, 1 being highest


class ComponentHealthMonitor:
    """Base class for component-specific health monitoring"""
    
    def __init__(self, component_id: str, component_type: ComponentType, window_size: int = 96):
        self.component_id = component_id
        self.component_type = component_type
        self.window_size = window_size  # Number of timesteps to keep in history
        
        # Historical data storage
        self.history = {
            'timestamp': deque(maxlen=window_size),
            'values': deque(maxlen=window_size),
            'status': deque(maxlen=window_size),
        }
        
        # Health metrics
        self.health_index = 100.0
        self.performance_index = 100.0
        self.reliability_index = 100.0
        self.degradation_rate = 0.0
        
        # Anomaly tracking
        self.anomaly_count = 0
        self.last_anomaly = None
        self.consecutive_anomalies = 0
        
        # Baseline statistics
        self.baseline_mean = None
        self.baseline_std = None
        self.baseline_established = False
        
    def update(self, value: float, timestamp: datetime):
        """Update with new measurement"""
        self.history['timestamp'].append(timestamp)
        self.history['values'].append(value)
        
        # Update baseline if we have enough data
        if not self.baseline_established and len(self.history['values']) >= 50:
            self._establish_baseline()
            
    def _establish_baseline(self):
        """Establish baseline statistics from historical data"""
        values = np.array(self.history['values'])
        self.baseline_mean = np.mean(values)
        self.baseline_std = np.std(values)
        self.baseline_established = True
        
    def detect_anomaly(self, value: float, threshold: float = 3.0) -> Optional[Anomaly]:
        """Detect anomaly using statistical methods (z-score)"""
        if not self.baseline_established:
            return None
            
        z_score = abs((value - self.baseline_mean) / (self.baseline_std + 1e-6))
        
        if z_score > threshold:
            severity = SeverityLevel.CRITICAL if z_score > 5.0 else SeverityLevel.WARNING
            
            anomaly = Anomaly(
                timestamp=datetime.now(),
                component_id=self.component_id,
                component_type=self.component_type,
                anomaly_type="statistical_deviation",
                severity=severity,
                description=f"Abnormal value detected: {value:.2f} (expected: {self.baseline_mean:.2f})",
                current_value=value,
                expected_value=self.baseline_mean,
                deviation=z_score,
                confidence=min(z_score / 10.0, 1.0)
            )
            
            self.anomaly_count += 1
            self.consecutive_anomalies += 1
            self.last_anomaly = anomaly
            
            return anomaly
        else:
            self.consecutive_anomalies = 0
            return None
            
    def get_health_index(self) -> HealthIndex:
        """Calculate and return current health index"""
        return HealthIndex(
            component_id=self.component_id,
            component_type=self.component_type,
            overall_health=self.health_index,
            performance_index=self.performance_index,
            reliability_index=self.reliability_index,
            degradation_rate=self.degradation_rate,
            estimated_remaining_life=self._estimate_remaining_life(),
            last_maintenance=None,
            next_maintenance_due=None
        )
        
    def _estimate_remaining_life(self) -> float:
        """Estimate remaining operational life in hours"""
        if self.degradation_rate <= 0:
            return float('inf')
        # Simple linear extrapolation
        return (self.health_index / self.degradation_rate) * 8760  # hours per year


class BatteryHealthMonitor(ComponentHealthMonitor):
    """Battery-specific health monitoring with degradation tracking"""
    
    def __init__(self, component_id: str, capacity_kwh: float, cycle_life: int = 5000):
        super().__init__(component_id, ComponentType.BATTERY)
        self.capacity_kwh = capacity_kwh
        self.nominal_cycle_life = cycle_life
        
        # Battery-specific metrics
        self.soh = 100.0  # State of Health
        self.soc = 50.0  # State of Charge
        self.temperature = 25.0
        self.cycles_completed = 0.0
        self.total_throughput_kwh = 0.0
        
        # Tracking for anomalies
        self.overcharge_count = 0
        self.deep_discharge_count = 0
        self.overtemperature_count = 0
        
    def update_battery_state(self, soc: float, soh: float, temperature: float, 
                            power_kw: float, timestep_hours: float = 0.25):
        """Update battery state with new measurements"""
        timestamp = datetime.now()
        
        self.soc = soc
        self.soh = soh
        self.temperature = temperature
        
        # Update throughput and cycles
        energy_kwh = abs(power_kw) * timestep_hours
        self.total_throughput_kwh += energy_kwh
        
        # Update health index based on SoH
        self.health_index = soh
        
        # Calculate degradation rate
        expected_soh = 100.0 - (self.cycles_completed / self.nominal_cycle_life) * 20  # 20% degradation
        self.degradation_rate = max(0, (100.0 - soh) / (self.cycles_completed / 8760 + 0.1))
        
        # Update history
        self.update(soh, timestamp)
        
    def detect_battery_anomalies(self) -> List[Anomaly]:
        """Detect battery-specific anomalies"""
        anomalies = []
        timestamp = datetime.now()
        
        # Check for overcharge
        if self.soc > 95.0:
            self.overcharge_count += 1
            anomalies.append(Anomaly(
                timestamp=timestamp,
                component_id=self.component_id,
                component_type=ComponentType.BATTERY,
                anomaly_type="overcharge",
                severity=SeverityLevel.WARNING,
                description=f"Battery SoC too high: {self.soc:.1f}%",
                current_value=self.soc,
                expected_value=90.0,
                deviation=self.soc - 90.0,
                confidence=0.95
            ))
            
        # Check for deep discharge
        if self.soc < 15.0:
            self.deep_discharge_count += 1
            anomalies.append(Anomaly(
                timestamp=timestamp,
                component_id=self.component_id,
                component_type=ComponentType.BATTERY,
                anomaly_type="deep_discharge",
                severity=SeverityLevel.WARNING,
                description=f"Battery SoC too low: {self.soc:.1f}%",
                current_value=self.soc,
                expected_value=20.0,
                deviation=20.0 - self.soc,
                confidence=0.95
            ))
            
        # Check for over-temperature
        if self.temperature > 45.0:
            self.overtemperature_count += 1
            severity = SeverityLevel.CRITICAL if self.temperature > 55.0 else SeverityLevel.WARNING
            anomalies.append(Anomaly(
                timestamp=timestamp,
                component_id=self.component_id,
                component_type=ComponentType.BATTERY,
                anomaly_type="over_temperature",
                severity=severity,
                description=f"Battery temperature too high: {self.temperature:.1f}°C",
                current_value=self.temperature,
                expected_value=35.0,
                deviation=self.temperature - 35.0,
                confidence=0.98
            ))
            
        # Check for rapid degradation
        if self.soh < 80.0:
            anomalies.append(Anomaly(
                timestamp=timestamp,
                component_id=self.component_id,
                component_type=ComponentType.BATTERY,
                anomaly_type="rapid_degradation",
                severity=SeverityLevel.CRITICAL,
                description=f"Battery nearing end of life: SoH = {self.soh:.1f}%",
                current_value=self.soh,
                expected_value=100.0,
                deviation=100.0 - self.soh,
                confidence=0.99
            ))
            
        return anomalies
        
    def get_maintenance_recommendation(self) -> Optional[MaintenanceRecommendation]:
        """Generate maintenance recommendation based on battery health"""
        if self.soh < 80.0:
            return MaintenanceRecommendation(
                component_id=self.component_id,
                component_type=ComponentType.BATTERY,
                recommendation_type="replacement",
                urgency=SeverityLevel.CRITICAL,
                description=f"Battery {self.component_id} has reached end of useful life (SoH: {self.soh:.1f}%)",
                estimated_time_to_failure=100.0,  # hours
                recommended_action="Schedule battery replacement within 1 week",
                estimated_downtime=8.0,  # hours
                estimated_cost=self.capacity_kwh * 15000,  # ₹15,000 per kWh
                risk_if_ignored="System unreliability, potential sudden failure, reduced capacity"
            )
        elif self.overtemperature_count > 10:
            return MaintenanceRecommendation(
                component_id=self.component_id,
                component_type=ComponentType.BATTERY,
                recommendation_type="inspection",
                urgency=SeverityLevel.WARNING,
                description=f"Battery {self.component_id} experiencing frequent overtemperature events",
                estimated_time_to_failure=500.0,
                recommended_action="Inspect cooling system, check thermal management",
                estimated_downtime=2.0,
                estimated_cost=5000.0,  # ₹5,000
                risk_if_ignored="Accelerated degradation, reduced lifespan, fire risk"
            )
        return None


class SolarPVHealthMonitor(ComponentHealthMonitor):
    """Solar PV system health monitoring"""
    
    def __init__(self, component_id: str, nominal_capacity_kw: float):
        super().__init__(component_id, ComponentType.SOLAR_PV)
        self.nominal_capacity_kw = nominal_capacity_kw
        
        # PV-specific metrics
        self.performance_ratio = 100.0  # %
        self.capacity_factor = 0.0
        self.irradiance = 0.0
        self.temperature = 25.0
        
        # Tracking
        self.low_performance_count = 0
        self.zero_output_daylight_count = 0
        
    def update_pv_state(self, power_output_kw: float, irradiance: float, 
                        ambient_temp: float, panel_temp: float):
        """Update PV system state"""
        timestamp = datetime.now()
        
        self.irradiance = irradiance
        self.temperature = panel_temp
        
        # Calculate expected output based on irradiance
        if irradiance > 100:  # W/m²
            expected_output = self.nominal_capacity_kw * (irradiance / 1000.0)
            actual_ratio = (power_output_kw / expected_output) if expected_output > 0 else 0
            self.performance_ratio = actual_ratio * 100.0
        else:
            self.performance_ratio = 100.0
            
        # Update health index
        self.health_index = min(100.0, self.performance_ratio)
        self.performance_index = self.performance_ratio
        
        # Update history
        self.update(power_output_kw, timestamp)
        
    def detect_pv_anomalies(self) -> List[Anomaly]:
        """Detect PV-specific anomalies"""
        anomalies = []
        timestamp = datetime.now()
        
        # Check for low performance during high irradiance
        if self.irradiance > 500 and self.performance_ratio < 70:
            self.low_performance_count += 1
            anomalies.append(Anomaly(
                timestamp=timestamp,
                component_id=self.component_id,
                component_type=ComponentType.SOLAR_PV,
                anomaly_type="low_performance",
                severity=SeverityLevel.WARNING,
                description=f"PV system underperforming: {self.performance_ratio:.1f}% (expected >75%)",
                current_value=self.performance_ratio,
                expected_value=80.0,
                deviation=80.0 - self.performance_ratio,
                confidence=0.85
            ))
            
        # Check for zero output during daylight
        if self.irradiance > 300 and len(self.history['values']) > 0:
            recent_output = list(self.history['values'])[-1]
            if recent_output < 1.0:
                self.zero_output_daylight_count += 1
                anomalies.append(Anomaly(
                    timestamp=timestamp,
                    component_id=self.component_id,
                    component_type=ComponentType.SOLAR_PV,
                    anomaly_type="zero_output",
                    severity=SeverityLevel.CRITICAL,
                    description="PV system producing no power during daylight hours",
                    current_value=recent_output,
                    expected_value=self.nominal_capacity_kw * 0.5,
                    deviation=100.0,
                    confidence=0.95
                ))
                
        # Check for overheating
        if self.temperature > 85.0:
            anomalies.append(Anomaly(
                timestamp=timestamp,
                component_id=self.component_id,
                component_type=ComponentType.SOLAR_PV,
                anomaly_type="overheating",
                severity=SeverityLevel.WARNING,
                description=f"PV panel temperature high: {self.temperature:.1f}°C",
                current_value=self.temperature,
                expected_value=65.0,
                deviation=self.temperature - 65.0,
                confidence=0.90
            ))
            
        return anomalies
        
    def get_maintenance_recommendation(self) -> Optional[MaintenanceRecommendation]:
        """Generate maintenance recommendation for PV system"""
        if self.low_performance_count > 20:
            return MaintenanceRecommendation(
                component_id=self.component_id,
                component_type=ComponentType.SOLAR_PV,
                recommendation_type="inspection",
                urgency=SeverityLevel.WARNING,
                description=f"PV system {self.component_id} showing persistent underperformance",
                estimated_time_to_failure=None,
                recommended_action="Clean panels, inspect for shading, check inverter connections, verify MPPT operation",
                estimated_downtime=4.0,
                estimated_cost=8000.0,  # ₹8,000
                risk_if_ignored="Continued energy loss, reduced ROI, potential equipment damage"
            )
        elif self.zero_output_daylight_count > 5:
            return MaintenanceRecommendation(
                component_id=self.component_id,
                component_type=ComponentType.SOLAR_PV,
                recommendation_type="repair",
                urgency=SeverityLevel.CRITICAL,
                description=f"PV system {self.component_id} has zero output during daylight",
                estimated_time_to_failure=0.0,
                recommended_action="Immediate inspection required - check inverter, wiring, and panel connections",
                estimated_downtime=6.0,
                estimated_cost=25000.0,  # ₹25,000
                risk_if_ignored="Complete loss of solar generation, grid dependency, increased costs"
            )
        return None


class EVChargerHealthMonitor(ComponentHealthMonitor):
    """EV Charger health monitoring"""
    
    def __init__(self, component_id: str, max_power_kw: float):
        super().__init__(component_id, ComponentType.EV_CHARGER)
        self.max_power_kw = max_power_kw
        
        # Charger-specific metrics
        self.efficiency = 95.0
        self.total_energy_delivered_kwh = 0.0
        self.charging_sessions = 0
        self.fault_count = 0
        
    def update_charger_state(self, power_output_kw: float, efficiency: float, 
                            temperature: float, fault_status: bool):
        """Update EV charger state"""
        timestamp = datetime.now()
        
        self.efficiency = efficiency
        self.temperature = temperature
        
        if fault_status:
            self.fault_count += 1
            
        # Update health based on efficiency and faults
        self.health_index = (efficiency / 95.0) * 100.0 * (1.0 - self.fault_count / 100.0)
        self.health_index = max(0.0, min(100.0, self.health_index))
        
        self.update(power_output_kw, timestamp)
        
    def detect_charger_anomalies(self) -> List[Anomaly]:
        """Detect EV charger anomalies"""
        anomalies = []
        timestamp = datetime.now()
        
        # Check for low efficiency
        if self.efficiency < 85.0:
            anomalies.append(Anomaly(
                timestamp=timestamp,
                component_id=self.component_id,
                component_type=ComponentType.EV_CHARGER,
                anomaly_type="low_efficiency",
                severity=SeverityLevel.WARNING,
                description=f"Charger efficiency degraded: {self.efficiency:.1f}%",
                current_value=self.efficiency,
                expected_value=92.0,
                deviation=92.0 - self.efficiency,
                confidence=0.85
            ))
            
        # Check for frequent faults
        if self.fault_count > 10:
            anomalies.append(Anomaly(
                timestamp=timestamp,
                component_id=self.component_id,
                component_type=ComponentType.EV_CHARGER,
                anomaly_type="frequent_faults",
                severity=SeverityLevel.CRITICAL,
                description=f"Charger experiencing frequent faults: {self.fault_count} occurrences",
                current_value=self.fault_count,
                expected_value=0,
                deviation=self.fault_count,
                confidence=0.95
            ))
            
        return anomalies


class AnomalyDetectionSystem:
    """
    Main anomaly detection and predictive maintenance system
    Coordinates all component monitors and provides unified interface
    """
    
    def __init__(self):
        self.component_monitors: Dict[str, ComponentHealthMonitor] = {}
        self.anomalies: List[Anomaly] = []
        self.maintenance_recommendations: List[MaintenanceRecommendation] = []
        self.diagnostic_insights: List[DiagnosticInsight] = []
        
        # Alert tracking
        self.active_alerts = []
        self.alert_history = []
        
        # Statistics
        self.total_anomalies_detected = 0
        self.critical_anomalies = 0
        
    def register_battery(self, battery_id: str, capacity_kwh: float, cycle_life: int = 5000):
        """Register a battery for monitoring"""
        monitor = BatteryHealthMonitor(battery_id, capacity_kwh, cycle_life)
        self.component_monitors[battery_id] = monitor
        return monitor
        
    def register_solar_pv(self, pv_id: str, nominal_capacity_kw: float):
        """Register a solar PV system for monitoring"""
        monitor = SolarPVHealthMonitor(pv_id, nominal_capacity_kw)
        self.component_monitors[pv_id] = monitor
        return monitor
        
    def register_ev_charger(self, charger_id: str, max_power_kw: float):
        """Register an EV charger for monitoring"""
        monitor = EVChargerHealthMonitor(charger_id, max_power_kw)
        self.component_monitors[charger_id] = monitor
        return monitor
        
    def update_component_state(self, component_id: str, **kwargs):
        """Update state for a specific component"""
        if component_id not in self.component_monitors:
            return
            
        monitor = self.component_monitors[component_id]
        
        if isinstance(monitor, BatteryHealthMonitor):
            monitor.update_battery_state(**kwargs)
        elif isinstance(monitor, SolarPVHealthMonitor):
            monitor.update_pv_state(**kwargs)
        elif isinstance(monitor, EVChargerHealthMonitor):
            monitor.update_charger_state(**kwargs)
            
    def detect_all_anomalies(self) -> List[Anomaly]:
        """Run anomaly detection on all components"""
        all_anomalies = []
        
        for component_id, monitor in self.component_monitors.items():
            if isinstance(monitor, BatteryHealthMonitor):
                anomalies = monitor.detect_battery_anomalies()
            elif isinstance(monitor, SolarPVHealthMonitor):
                anomalies = monitor.detect_pv_anomalies()
            elif isinstance(monitor, EVChargerHealthMonitor):
                anomalies = monitor.detect_charger_anomalies()
            else:
                anomalies = []
                
            all_anomalies.extend(anomalies)
            
            # Track statistics
            for anomaly in anomalies:
                self.total_anomalies_detected += 1
                if anomaly.severity == SeverityLevel.CRITICAL:
                    self.critical_anomalies += 1
                    
        self.anomalies.extend(all_anomalies)
        return all_anomalies
        
    def generate_maintenance_recommendations(self) -> List[MaintenanceRecommendation]:
        """Generate maintenance recommendations for all components"""
        recommendations = []
        
        for component_id, monitor in self.component_monitors.items():
            if hasattr(monitor, 'get_maintenance_recommendation'):
                rec = monitor.get_maintenance_recommendation()
                if rec is not None:
                    recommendations.append(rec)
                    
        self.maintenance_recommendations = recommendations
        return recommendations
        
    def get_all_health_indices(self) -> Dict[str, HealthIndex]:
        """Get health indices for all components"""
        health_indices = {}
        
        for component_id, monitor in self.component_monitors.items():
            health_indices[component_id] = monitor.get_health_index()
            
        return health_indices
        
    def get_system_health_summary(self) -> Dict:
        """Get overall system health summary"""
        health_indices = self.get_all_health_indices()
        
        if not health_indices:
            return {
                'overall_health': 100.0,
                'components_monitored': 0,
                'critical_components': 0,
                'warning_components': 0
            }
            
        overall_health = np.mean([h.overall_health for h in health_indices.values()])
        critical_count = sum(1 for h in health_indices.values() if h.overall_health < 70)
        warning_count = sum(1 for h in health_indices.values() if 70 <= h.overall_health < 85)
        
        return {
            'overall_health': overall_health,
            'components_monitored': len(health_indices),
            'critical_components': critical_count,
            'warning_components': warning_count,
            'total_anomalies': self.total_anomalies_detected,
            'critical_anomalies': self.critical_anomalies,
            'active_recommendations': len(self.maintenance_recommendations)
        }
        
    def generate_diagnostic_insights(self) -> List[DiagnosticInsight]:
        """Generate diagnostic insights based on anomalies and health indices"""
        insights = []
        health_indices = self.get_all_health_indices()
        
        for component_id, health in health_indices.items():
            monitor = self.component_monitors[component_id]
            
            # Battery-specific insights
            if isinstance(monitor, BatteryHealthMonitor):
                if health.overall_health < 80:
                    insights.append(DiagnosticInsight(
                        component_id=component_id,
                        component_type=ComponentType.BATTERY,
                        issue="Battery nearing end of life",
                        root_cause=f"SoH degraded to {health.overall_health:.1f}% due to cycling and aging",
                        impact="Reduced storage capacity, unreliable backup power",
                        recommended_action="Plan for battery replacement within 1-2 months",
                        priority=1
                    ))
                elif monitor.overtemperature_count > 10:
                    insights.append(DiagnosticInsight(
                        component_id=component_id,
                        component_type=ComponentType.BATTERY,
                        issue="Frequent overtemperature events",
                        root_cause="Insufficient cooling or high ambient temperature",
                        impact="Accelerated degradation, reduced lifespan",
                        recommended_action="Inspect and upgrade cooling system",
                        priority=2
                    ))
                    
            # Solar PV insights
            elif isinstance(monitor, SolarPVHealthMonitor):
                if monitor.low_performance_count > 20:
                    insights.append(DiagnosticInsight(
                        component_id=component_id,
                        component_type=ComponentType.SOLAR_PV,
                        issue="Persistent underperformance",
                        root_cause="Possible soiling, shading, or equipment degradation",
                        impact=f"Lost generation: ~{(100 - health.performance_index):.0f}% capacity reduction",
                        recommended_action="Clean panels, check for shading, inspect inverter",
                        priority=2
                    ))
                    
        self.diagnostic_insights = insights
        return insights
        
    def get_actionable_alerts(self) -> List[Dict]:
        """Get actionable alerts with recommended actions"""
        alerts = []
        
        # From anomalies
        for anomaly in self.anomalies[-50:]:  # Last 50 anomalies
            if anomaly.severity in [SeverityLevel.CRITICAL, SeverityLevel.WARNING]:
                action = self._get_recommended_action_for_anomaly(anomaly)
                alerts.append({
                    'timestamp': anomaly.timestamp,
                    'component': anomaly.component_id,
                    'type': anomaly.anomaly_type,
                    'severity': anomaly.severity.value,
                    'description': anomaly.description,
                    'recommended_action': action
                })
                
        return alerts
        
    def _get_recommended_action_for_anomaly(self, anomaly: Anomaly) -> str:
        """Get recommended action for an anomaly"""
        action_map = {
            'overcharge': "Reduce charging power, check BMS settings",
            'deep_discharge': "Switch load to grid, prevent further discharge",
            'over_temperature': "Activate cooling, reduce power throughput",
            'rapid_degradation': "Schedule maintenance inspection immediately",
            'low_performance': "Clean panels, check inverter connections",
            'zero_output': "Emergency inspection - check inverter and wiring",
            'overheating': "Check ventilation, reduce load if possible",
            'low_efficiency': "Schedule calibration and component check",
            'frequent_faults': "Replace or repair charger unit"
        }
        
        return action_map.get(anomaly.anomaly_type, "Contact maintenance team for inspection")
        
    def reset(self):
        """Reset all tracking for new episode"""
        for monitor in self.component_monitors.values():
            monitor.anomaly_count = 0
            monitor.consecutive_anomalies = 0
            
    def get_monitoring_report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        health_indices = self.get_all_health_indices()
        system_summary = self.get_system_health_summary()
        recommendations = self.generate_maintenance_recommendations()
        insights = self.generate_diagnostic_insights()
        alerts = self.get_actionable_alerts()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_summary': system_summary,
            'health_indices': {k: {
                'overall_health': v.overall_health,
                'performance_index': v.performance_index,
                'reliability_index': v.reliability_index,
                'degradation_rate': v.degradation_rate
            } for k, v in health_indices.items()},
            'active_alerts': alerts,
            'maintenance_recommendations': [{
                'component': r.component_id,
                'type': r.recommendation_type,
                'urgency': r.urgency.value,
                'description': r.description,
                'action': r.recommended_action,
                'cost': r.estimated_cost
            } for r in recommendations],
            'diagnostic_insights': [{
                'component': i.component_id,
                'issue': i.issue,
                'root_cause': i.root_cause,
                'impact': i.impact,
                'action': i.recommended_action,
                'priority': i.priority
            } for i in insights]
        }
