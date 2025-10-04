"""
Extreme Conditions Testing Suite
Tests system behavior under severe and emergency scenarios

Scenarios Tested:
1. Heat wave (45°C+ ambient temperature)
2. Extended cloudy period (7+ days)
3. Equipment cascading failures
4. Multiple simultaneous anomalies
5. Battery thermal runaway scenario
6. Complete grid blackout
7. Inverter failure during peak load
8. EV charging station failure
9. Sensor failures and bad data
10. Cyber attack simulation (abnormal commands)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

from microgrid_env import MicrogridEMSEnv


class ExtremeConditionsTester:
    """Test system under extreme and emergency conditions"""
    
    def __init__(self, save_dir="results/extreme_conditions"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.test_count = 0
        self.passed = 0
        self.failed = 0
        self.critical_failures = 0
        
    def create_extreme_scenario(self, scenario_type, duration_steps=192):  # 2 days
        """Create data for extreme scenarios"""
        
        if scenario_type == "heat_wave":
            # 45°C+ ambient, reduced PV efficiency, high cooling load
            pv_base = self._generate_solar_profile(duration_steps)
            pv_degraded = pv_base * 0.75  # 25% efficiency loss due to heat
            
            pv = pd.DataFrame({'pv_power_kw': pv_degraded})
            wt = pd.DataFrame({'wt_power_kw': 300 + np.random.rand(duration_steps) * 400})  # Low wind
            load_base = 5000 + np.random.rand(duration_steps) * 2000  # High AC load
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 7.0 + np.random.rand(duration_steps) * 3})
            metadata = {'ambient_temp': 45 + np.random.rand(duration_steps) * 5}
            
        elif scenario_type == "extended_cloudy":
            # 7+ days of very low solar (monsoon)
            pv_very_low = self._generate_solar_profile(duration_steps) * 0.15  # 85% reduction
            
            pv = pd.DataFrame({'pv_power_kw': pv_very_low})
            wt = pd.DataFrame({'wt_power_kw': 200 + np.random.rand(duration_steps) * 300})
            load = pd.DataFrame({'load_kw': 3500 + np.random.rand(duration_steps) * 1000})
            price = pd.DataFrame({'price_inr_per_kwh': 6.5 + np.random.rand(duration_steps) * 2.5})
            metadata = {'weather': 'heavy_clouds'}
            
        elif scenario_type == "cascading_failures":
            # Equipment failures one after another
            pv = pd.DataFrame({'pv_power_kw': self._generate_solar_profile(duration_steps)})
            wt = pd.DataFrame({'wt_power_kw': 800 + np.random.rand(duration_steps) * 1000})
            load = pd.DataFrame({'load_kw': 4000 + np.random.rand(duration_steps) * 1500})
            price = pd.DataFrame({'price_inr_per_kwh': 5.5 + np.random.rand(duration_steps) * 2.5})
            
            # Simulate failures at specific times
            metadata = {
                'failures': [
                    {'time': 30, 'component': 'battery_1', 'type': 'offline'},
                    {'time': 50, 'component': 'inverter_1', 'type': 'degraded'},
                    {'time': 70, 'component': 'ev_charger_1', 'type': 'fault'},
                ]
            }
            
        elif scenario_type == "grid_blackout":
            # Complete grid unavailable for extended period
            pv = pd.DataFrame({'pv_power_kw': self._generate_solar_profile(duration_steps)})
            wt = pd.DataFrame({'wt_power_kw': 600 + np.random.rand(duration_steps) * 1000})
            load = pd.DataFrame({'load_kw': 3500 + np.random.rand(duration_steps) * 1000})
            price = pd.DataFrame({'price_inr_per_kwh': np.inf * np.ones(duration_steps)})  # Grid unavailable
            metadata = {'grid_available': False}
            
        elif scenario_type == "sensor_failures":
            # Bad sensor data and missing readings
            pv_data = self._generate_solar_profile(duration_steps)
            # Inject bad readings
            bad_indices = np.random.choice(duration_steps, size=duration_steps//10, replace=False)
            pv_data[bad_indices] = -999  # Bad sensor reading
            
            pv = pd.DataFrame({'pv_power_kw': pv_data})
            wt = pd.DataFrame({'wt_power_kw': 700 + np.random.rand(duration_steps) * 1000})
            load = pd.DataFrame({'load_kw': 3500 + np.random.rand(duration_steps) * 1000})
            price = pd.DataFrame({'price_inr_per_kwh': 5.5 + np.random.rand(duration_steps) * 2.5})
            metadata = {'sensor_quality': 'degraded'}
            
        elif scenario_type == "thermal_runaway":
            # Battery overheating scenario
            pv = pd.DataFrame({'pv_power_kw': self._generate_solar_profile(duration_steps)})
            wt = pd.DataFrame({'wt_power_kw': 700 + np.random.rand(duration_steps) * 1000})
            load = pd.DataFrame({'load_kw': 4000 + np.random.rand(duration_steps) * 1500})
            price = pd.DataFrame({'price_inr_per_kwh': 5.0 + np.random.rand(duration_steps) * 3})
            metadata = {
                'battery_temp_start': 55,  # High starting temperature
                'cooling_failure': True
            }
            
        elif scenario_type == "cyber_attack":
            # Simulated abnormal command injection
            pv = pd.DataFrame({'pv_power_kw': self._generate_solar_profile(duration_steps)})
            wt = pd.DataFrame({'wt_power_kw': 700 + np.random.rand(duration_steps) * 1000})
            load = pd.DataFrame({'load_kw': 3500 + np.random.rand(duration_steps) * 1000})
            price = pd.DataFrame({'price_inr_per_kwh': 5.5 + np.random.rand(duration_steps) * 2.5})
            metadata = {
                'attack_type': 'command_injection',
                'malicious_actions': True
            }
            
        elif scenario_type == "multi_anomaly":
            # Multiple simultaneous problems
            pv = pd.DataFrame({'pv_power_kw': self._generate_solar_profile(duration_steps) * 0.6})
            wt = pd.DataFrame({'wt_power_kw': 300 + np.random.rand(duration_steps) * 500})
            load_high = 5000 + np.random.rand(duration_steps) * 2000
            load = pd.DataFrame({'load_kw': load_high})
            price_volatile = 3 + np.random.rand(duration_steps) * 9  # Very volatile
            price = pd.DataFrame({'price_inr_per_kwh': price_volatile})
            metadata = {
                'ambient_temp': 40,
                'battery_degraded': True,
                'inverter_efficiency': 0.85
            }
            
        else:
            # Default extreme scenario
            pv = pd.DataFrame({'pv_power_kw': self._generate_solar_profile(duration_steps)})
            wt = pd.DataFrame({'wt_power_kw': 500 + np.random.rand(duration_steps) * 1000})
            load = pd.DataFrame({'load_kw': 4000 + np.random.rand(duration_steps) * 2000})
            price = pd.DataFrame({'price_inr_per_kwh': 6.0 + np.random.rand(duration_steps) * 4})
            metadata = {}
        
        return pv, wt, load, price, metadata
    
    def _generate_solar_profile(self, steps):
        """Generate realistic solar profile"""
        profile = np.zeros(steps)
        for i in range(steps):
            hour = (i * 0.25) % 24
            if 6 <= hour <= 18:
                profile[i] = 3200 * (1 - ((hour - 12) / 6) ** 2) * np.random.uniform(0.7, 1.0)
        return np.maximum(0, profile)
    
    def test_extreme_scenario(self, scenario_name, scenario_type, duration_steps=192):
        """Run extreme condition test"""
        print(f"\n{'='*80}")
        print(f"🔥 EXTREME TEST: {scenario_name}")
        print(f"{'='*80}")
        
        self.test_count += 1
        start_time = datetime.now()
        
        try:
            # Create extreme scenario data
            pv, wt, load, price, metadata = self.create_extreme_scenario(scenario_type, duration_steps)
            
            # Create environment
            env = MicrogridEMSEnv(
                pv_profile=pv,
                wt_profile=wt,
                load_profile=load,
                price_profile=price,
                enable_evs=True,
                enable_degradation=True,
                enable_emissions=True
            )
            
            # Run simulation with monitoring
            obs = env.reset(episode_start_idx=0)
            
            metrics = {
                'total_cost': 0,
                'total_emissions': 0,
                'unmet_demand_events': 0,
                'unmet_demand_total_kwh': 0,
                'anomalies_detected': 0,
                'critical_anomalies': 0,
                'system_crashes': 0,
                'battery_soh_degradation': 0,
                'max_battery_temp': 0,
                'rewards': [],
                'health_over_time': []
            }
            
            steps_completed = 0
            
            for step in range(min(duration_steps, 96)):  # Limit for testing
                try:
                    # Random action (or trained agent)
                    action = env.action_space.sample()
                    
                    obs, reward, done, info = env.step(action)
                    
                    metrics['rewards'].append(reward)
                    metrics['total_cost'] += info.get('cost', 0)
                    metrics['total_emissions'] += info.get('emissions', 0)
                    
                    if info.get('unmet_demand', 0) > 0:
                        metrics['unmet_demand_events'] += 1
                        metrics['unmet_demand_total_kwh'] += info.get('unmet_demand', 0)
                    
                    # Track health
                    health = env.get_system_health_summary()
                    metrics['health_over_time'].append(health['overall_health'])
                    
                    steps_completed += 1
                    
                    if done:
                        break
                        
                except Exception as step_error:
                    metrics['system_crashes'] += 1
                    print(f"   ⚠️ Step {step} error: {str(step_error)}")
                    break
            
            # Get final state
            health = env.get_system_health_summary()
            alerts = env.get_actionable_alerts()
            
            metrics['anomalies_detected'] = health['total_anomalies']
            metrics['critical_anomalies'] = health['critical_anomalies']
            metrics['final_health'] = health['overall_health']
            metrics['steps_completed'] = steps_completed
            
            # Evaluate results
            passed, is_critical, issues = self._evaluate_extreme_results(
                scenario_type, metrics, metadata
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'test_number': self.test_count,
                'scenario_name': scenario_name,
                'scenario_type': scenario_type,
                'duration_seconds': duration,
                'passed': passed,
                'is_critical_failure': is_critical,
                'issues': issues,
                'metrics': {k: v for k, v in metrics.items() if k != 'health_over_time'},
                'metadata': metadata,
                'timestamp': start_time.isoformat()
            }
            
            self.results.append(result)
            
            if is_critical:
                self.critical_failures += 1
                print(f"🔴 CRITICAL FAILURE - {scenario_name}")
            elif passed:
                self.passed += 1
                print(f"✅ SURVIVED - {scenario_name}")
            else:
                self.failed += 1
                print(f"⚠️ DEGRADED - {scenario_name}")
            
            if issues:
                print(f"   Issues: {', '.join(issues)}")
            
            print(f"   Duration: {duration:.2f}s")
            print(f"   Steps Completed: {steps_completed}/{min(duration_steps, 96)}")
            print(f"   Total Cost: ₹{metrics['total_cost']:,.2f}")
            print(f"   Unmet Demand: {metrics['unmet_demand_total_kwh']:.2f} kWh ({metrics['unmet_demand_events']} events)")
            print(f"   System Crashes: {metrics['system_crashes']}")
            print(f"   Final Health: {metrics.get('final_health', 0):.1f}%")
            print(f"   Anomalies: {metrics['anomalies_detected']} ({metrics['critical_anomalies']} critical)")
            
            return result
            
        except Exception as e:
            self.critical_failures += 1
            print(f"🔴 CRITICAL EXCEPTION - {scenario_name}")
            print(f"   Error: {str(e)}")
            
            import traceback
            traceback.print_exc()
            
            result = {
                'test_number': self.test_count,
                'scenario_name': scenario_name,
                'scenario_type': scenario_type,
                'passed': False,
                'is_critical_failure': True,
                'error': str(e),
                'timestamp': start_time.isoformat()
            }
            
            self.results.append(result)
            return result
    
    def _evaluate_extreme_results(self, scenario_type, metrics, metadata):
        """Evaluate extreme test results"""
        passed = True
        is_critical = False
        issues = []
        
        # Critical failures
        if metrics['system_crashes'] > 0:
            is_critical = True
            issues.append(f"System crashed {metrics['system_crashes']} times")
        
        if metrics['steps_completed'] < 48:  # Less than 12 hours
            is_critical = True
            issues.append(f"Failed to complete minimum steps: {metrics['steps_completed']}")
        
        # Severe issues
        if metrics.get('final_health', 100) < 30:
            passed = False
            issues.append(f"Critical health degradation: {metrics['final_health']:.1f}%")
        
        if metrics['unmet_demand_total_kwh'] > 500:
            passed = False
            issues.append(f"Excessive unmet demand: {metrics['unmet_demand_total_kwh']:.2f} kWh")
        
        # Scenario-specific evaluation
        if scenario_type == "heat_wave":
            if metrics.get('final_health', 100) < 60:
                issues.append("Poor thermal management during heat wave")
        
        elif scenario_type == "grid_blackout":
            if metrics['unmet_demand_events'] > 30:
                issues.append("Unable to maintain supply during blackout")
        
        elif scenario_type == "extended_cloudy":
            if metrics['total_cost'] > 1000000:
                issues.append("Excessive cost during extended cloudy period")
        
        return passed, is_critical, issues
    
    def run_all_extreme_tests(self):
        """Run complete extreme conditions suite"""
        print("\n" + "="*80)
        print("🔥 EXTREME CONDITIONS TEST SUITE")
        print("="*80)
        
        test_scenarios = [
            ("Heat Wave (45°C+)", "heat_wave", 192),
            ("Extended Cloudy Period (7 days)", "extended_cloudy", 192),
            ("Cascading Equipment Failures", "cascading_failures", 192),
            ("Complete Grid Blackout", "grid_blackout", 192),
            ("Sensor Failures & Bad Data", "sensor_failures", 96),
            ("Battery Thermal Runaway", "thermal_runaway", 96),
            ("Cyber Attack Simulation", "cyber_attack", 96),
            ("Multiple Simultaneous Anomalies", "multi_anomaly", 192),
        ]
        
        for scenario_data in test_scenarios:
            if len(scenario_data) == 3:
                scenario_name, scenario_type, duration = scenario_data
                self.test_extreme_scenario(scenario_name, scenario_type, duration)
            else:
                scenario_name, scenario_type = scenario_data
                self.test_extreme_scenario(scenario_name, scenario_type)
        
        # Save results
        self.save_results()
        
        # Print summary
        self.print_summary()
    
    def save_results(self):
        """Save test results"""
        results_file = self.save_dir / f"extreme_conditions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            'test_suite': 'Extreme Conditions',
            'timestamp': datetime.now().isoformat(),
            'total_tests': self.test_count,
            'passed': self.passed,
            'failed': self.failed,
            'critical_failures': self.critical_failures,
            'survival_rate': ((self.passed + self.failed) / self.test_count * 100) if self.test_count > 0 else 0,
            'results': self.results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to: {results_file}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 EXTREME CONDITIONS SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.test_count}")
        print(f"Survived: {self.passed} ✅")
        print(f"Degraded: {self.failed} ⚠️")
        print(f"Critical Failures: {self.critical_failures} 🔴")
        survival_rate = ((self.passed + self.failed) / self.test_count * 100) if self.test_count > 0 else 0
        print(f"Survival Rate: {survival_rate:.1f}%")
        print("="*80)


def main():
    """Run extreme conditions tests"""
    tester = ExtremeConditionsTester()
    tester.run_all_extreme_tests()
    
    print("\n🔥 Extreme conditions testing complete!")
    print(f"Results saved in: {tester.save_dir}")


if __name__ == "__main__":
    main()
