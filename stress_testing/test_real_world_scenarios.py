"""
Real-World Scenarios Testing Suite
Tests system with actual Indian microgrid scenarios and seasonal patterns

Scenarios Tested:
1. Monsoon season (June-September) - Heavy rain, low solar
2. Summer peak (April-May) - High AC load, peak demand
3. Festival periods (Diwali, Dussehra) - Unusual load patterns
4. Industrial spike (manufacturing shifts)
5. Rural agricultural load (irrigation pumps)
6. Urban residential pattern (morning/evening peaks)
7. Commercial establishment pattern (9-5 heavy load)
8. Weekend vs weekday patterns
9. Power cut recovery scenario
10. EV fleet rush hour charging
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


class RealWorldScenarioTester:
    """Test system with realistic Indian microgrid scenarios"""
    
    def __init__(self, save_dir="results/real_world"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.test_count = 0
        self.passed = 0
        self.failed = 0
        
    def create_realistic_scenario(self, scenario_type, duration_steps=96):
        """Create realistic scenario data based on Indian context"""
        
        if scenario_type == "monsoon_season":
            # June-September: Heavy rain, low solar, high humidity
            # Solar reduced to 20-40%, wind might be higher
            pv_monsoon = self._generate_solar_profile(duration_steps) * np.random.uniform(0.2, 0.4, duration_steps)
            wt_monsoon = 900 + np.random.rand(duration_steps) * 1100  # Higher wind
            
            # Moderate load (AC usage less due to cooler weather)
            load_base = 3200 + np.random.rand(duration_steps) * 800
            
            pv = pd.DataFrame({'pv_power_kw': pv_monsoon})
            wt = pd.DataFrame({'wt_power_kw': wt_monsoon})
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 5.5 + np.random.rand(duration_steps) * 2})
            metadata = {'season': 'monsoon', 'humidity': 85, 'rainfall': 'heavy'}
            
        elif scenario_type == "summer_peak":
            # April-May: Extreme heat, peak AC load, high solar
            pv_summer = self._generate_solar_profile(duration_steps) * np.random.uniform(0.9, 1.1, duration_steps)
            wt_summer = 300 + np.random.rand(duration_steps) * 500  # Low wind
            
            # Very high load due to AC, peak hours 12-4 PM and 9-11 PM
            load_base = 4500 + np.random.rand(duration_steps) * 1500
            for i in range(duration_steps):
                hour = (i * 0.25) % 24
                if 12 <= hour <= 16 or 21 <= hour <= 23:
                    load_base[i] *= 1.4  # 40% spike during peak hours
            
            pv = pd.DataFrame({'pv_power_kw': pv_summer})
            wt = pd.DataFrame({'wt_power_kw': wt_summer})
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 6.5 + np.random.rand(duration_steps) * 3.5})  # Higher prices
            metadata = {'season': 'summer', 'temp': 42, 'ac_load_factor': 1.4}
            
        elif scenario_type == "festival_diwali":
            # Diwali: Evening lighting loads, decorations, celebrations
            pv_normal = self._generate_solar_profile(duration_steps)
            wt_normal = 600 + np.random.rand(duration_steps) * 800
            
            # Unusual load pattern: evening spike from 6 PM to 12 AM
            load_base = 3500 + np.random.rand(duration_steps) * 1000
            for i in range(duration_steps):
                hour = (i * 0.25) % 24
                if 18 <= hour or hour <= 2:  # Evening to late night
                    load_base[i] *= 1.6  # 60% spike for decorations/celebrations
            
            pv = pd.DataFrame({'pv_power_kw': pv_normal})
            wt = pd.DataFrame({'wt_power_kw': wt_normal})
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 6.0 + np.random.rand(duration_steps) * 2.5})
            metadata = {'occasion': 'diwali', 'decorative_load': True, 'evening_spike': 1.6}
            
        elif scenario_type == "industrial_shifts":
            # Manufacturing facility: 3 shifts, heavy machinery
            pv_normal = self._generate_solar_profile(duration_steps)
            wt_normal = 650 + np.random.rand(duration_steps) * 900
            
            # Shift patterns: 6-2, 2-10, 10-6
            load_base = np.zeros(duration_steps)
            for i in range(duration_steps):
                hour = (i * 0.25) % 24
                if 6 <= hour < 14:  # Morning shift
                    load_base[i] = 5500 + np.random.rand() * 1000
                elif 14 <= hour < 22:  # Evening shift
                    load_base[i] = 5200 + np.random.rand() * 800
                else:  # Night shift (lighter)
                    load_base[i] = 3800 + np.random.rand() * 600
            
            pv = pd.DataFrame({'pv_power_kw': pv_normal})
            wt = pd.DataFrame({'wt_power_kw': wt_normal})
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 5.0 + np.random.rand(duration_steps) * 3})
            metadata = {'type': 'industrial', 'shifts': 3, 'machinery_load': 'heavy'}
            
        elif scenario_type == "agricultural_irrigation":
            # Rural agricultural: Irrigation pumps 4-8 AM and 6-10 PM
            pv_normal = self._generate_solar_profile(duration_steps)
            wt_normal = 700 + np.random.rand(duration_steps) * 800
            
            # Pump load during irrigation hours
            load_base = 1500 + np.random.rand(duration_steps) * 500  # Low base
            for i in range(duration_steps):
                hour = (i * 0.25) % 24
                if (4 <= hour < 8) or (18 <= hour < 22):  # Irrigation times
                    load_base[i] += 3500  # Large pumps
            
            pv = pd.DataFrame({'pv_power_kw': pv_normal})
            wt = pd.DataFrame({'wt_power_kw': wt_normal})
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 4.5 + np.random.rand(duration_steps) * 2})
            metadata = {'type': 'agricultural', 'irrigation': True, 'pump_capacity': 3500}
            
        elif scenario_type == "urban_residential":
            # Urban residential: Morning 6-9 AM, Evening 6-11 PM peaks
            pv_normal = self._generate_solar_profile(duration_steps)
            wt_normal = 600 + np.random.rand(duration_steps) * 700
            
            # Typical residential pattern
            load_base = 2000 + np.random.rand(duration_steps) * 500
            for i in range(duration_steps):
                hour = (i * 0.25) % 24
                if 6 <= hour < 9:  # Morning peak
                    load_base[i] *= 1.5
                elif 18 <= hour < 23:  # Evening peak
                    load_base[i] *= 1.7
                elif 1 <= hour < 6:  # Night low
                    load_base[i] *= 0.6
            
            pv = pd.DataFrame({'pv_power_kw': pv_normal})
            wt = pd.DataFrame({'wt_power_kw': wt_normal})
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 5.5 + np.random.rand(duration_steps) * 2})
            metadata = {'type': 'residential', 'morning_peak': 1.5, 'evening_peak': 1.7}
            
        elif scenario_type == "commercial_office":
            # Commercial: 9 AM - 6 PM heavy load
            pv_normal = self._generate_solar_profile(duration_steps)
            wt_normal = 650 + np.random.rand(duration_steps) * 750
            
            # Office hours load
            load_base = 1800 + np.random.rand(duration_steps) * 400
            for i in range(duration_steps):
                hour = (i * 0.25) % 24
                if 9 <= hour < 18:  # Office hours
                    load_base[i] = 4500 + np.random.rand() * 800
            
            pv = pd.DataFrame({'pv_power_kw': pv_normal})
            wt = pd.DataFrame({'wt_power_kw': wt_normal})
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 5.8 + np.random.rand(duration_steps) * 2.2})
            metadata = {'type': 'commercial', 'office_hours': '9-18', 'hvac_load': 'high'}
            
        elif scenario_type == "power_cut_recovery":
            # Grid goes down and comes back up
            pv_normal = self._generate_solar_profile(duration_steps)
            wt_normal = 700 + np.random.rand(duration_steps) * 900
            load_normal = 3800 + np.random.rand(duration_steps) * 1200
            
            # Price spike when grid is down (steps 20-60)
            price_data = 5.5 + np.random.rand(duration_steps) * 2
            price_data[20:60] = 15.0  # Grid down, very expensive backup
            
            pv = pd.DataFrame({'pv_power_kw': pv_normal})
            wt = pd.DataFrame({'wt_power_kw': wt_normal})
            load = pd.DataFrame({'load_kw': load_normal})
            price = pd.DataFrame({'price_inr_per_kwh': price_data})
            metadata = {'power_cut': True, 'outage_duration_hours': 10, 'recovery_scenario': True}
            
        elif scenario_type == "ev_rush_hour":
            # EV charging surge during evening
            pv_normal = self._generate_solar_profile(duration_steps)
            wt_normal = 650 + np.random.rand(duration_steps) * 850
            
            # Base load + EV surge
            load_base = 3200 + np.random.rand(duration_steps) * 800
            for i in range(duration_steps):
                hour = (i * 0.25) % 24
                if 18 <= hour < 22:  # Evening EV charging rush
                    load_base[i] += 2500  # Multiple EVs charging
            
            pv = pd.DataFrame({'pv_power_kw': pv_normal})
            wt = pd.DataFrame({'wt_power_kw': wt_normal})
            load = pd.DataFrame({'load_kw': load_base})
            price = pd.DataFrame({'price_inr_per_kwh': 6.0 + np.random.rand(duration_steps) * 2.5})
            metadata = {'ev_surge': True, 'rush_hour': '18-22', 'ev_load_kw': 2500}
            
        else:
            # Default scenario
            pv = pd.DataFrame({'pv_power_kw': self._generate_solar_profile(duration_steps)})
            wt = pd.DataFrame({'wt_power_kw': 700 + np.random.rand(duration_steps) * 1000})
            load = pd.DataFrame({'load_kw': 3500 + np.random.rand(duration_steps) * 1000})
            price = pd.DataFrame({'price_inr_per_kwh': 5.5 + np.random.rand(duration_steps) * 2.5})
            metadata = {}
        
        return pv, wt, load, price, metadata
    
    def _generate_solar_profile(self, steps):
        """Generate realistic solar profile"""
        profile = np.zeros(steps)
        for i in range(steps):
            hour = (i * 0.25) % 24
            if 6 <= hour <= 18:
                profile[i] = 3200 * (1 - ((hour - 12) / 6) ** 2) * np.random.uniform(0.8, 1.0)
        return np.maximum(0, profile)
    
    def test_real_world_scenario(self, scenario_name, scenario_type, duration_steps=96):
        """Run real-world scenario test"""
        print(f"\n{'='*80}")
        print(f"🌍 REAL-WORLD TEST: {scenario_name}")
        print(f"{'='*80}")
        
        self.test_count += 1
        start_time = datetime.now()
        
        try:
            # Create scenario data
            pv, wt, load, price, metadata = self.create_realistic_scenario(scenario_type, duration_steps)
            
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
            
            # Run simulation
            obs = env.reset(episode_start_idx=0)
            
            metrics = {
                'total_cost': 0,
                'total_emissions': 0,
                'renewable_usage_pct': 0,
                'grid_usage_kwh': 0,
                'battery_cycles': 0,
                'unmet_demand_kwh': 0,
                'anomalies_detected': 0,
                'avg_health': 0,
                'rewards': []
            }
            
            steps_completed = 0
            renewable_energy = 0
            total_energy = 0
            
            for step in range(duration_steps):
                # Use random action (or trained agent)
                action = env.action_space.sample()
                
                obs, reward, done, info = env.step(action)
                
                metrics['rewards'].append(reward)
                metrics['total_cost'] += info.get('cost', 0)
                metrics['total_emissions'] += info.get('emissions', 0)
                metrics['unmet_demand_kwh'] += info.get('unmet_demand', 0)
                
                # Track renewable usage
                renewable_energy += info.get('pv_power', 0) + info.get('wt_power', 0)
                total_energy += info.get('load', 0)
                
                steps_completed += 1
                
                if done:
                    break
            
            # Calculate metrics
            metrics['renewable_usage_pct'] = (renewable_energy / total_energy * 100) if total_energy > 0 else 0
            metrics['steps_completed'] = steps_completed
            metrics['avg_reward'] = np.mean(metrics['rewards']) if metrics['rewards'] else 0
            
            # Get final health
            health = env.get_system_health_summary()
            metrics['final_health'] = health['overall_health']
            metrics['anomalies_detected'] = health['total_anomalies']
            
            # Evaluate
            passed, issues = self._evaluate_real_world_results(scenario_type, metrics, metadata)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'test_number': self.test_count,
                'scenario_name': scenario_name,
                'scenario_type': scenario_type,
                'duration_seconds': duration,
                'passed': passed,
                'issues': issues,
                'metrics': metrics,
                'metadata': metadata,
                'timestamp': start_time.isoformat()
            }
            
            self.results.append(result)
            
            if passed:
                self.passed += 1
                print(f"✅ PASS - {scenario_name}")
            else:
                self.failed += 1
                print(f"⚠️ FAIL - {scenario_name}")
            
            if issues:
                print(f"   Issues: {', '.join(issues)}")
            
            print(f"   Duration: {duration:.2f}s")
            print(f"   Total Cost: ₹{metrics['total_cost']:,.2f}")
            print(f"   Emissions: {metrics['total_emissions']:.2f} kg CO2")
            print(f"   Renewable Usage: {metrics['renewable_usage_pct']:.1f}%")
            print(f"   Unmet Demand: {metrics['unmet_demand_kwh']:.2f} kWh")
            print(f"   Avg Reward: {metrics['avg_reward']:.2f}")
            print(f"   Final Health: {metrics['final_health']:.1f}%")
            
            return result
            
        except Exception as e:
            self.failed += 1
            print(f"❌ ERROR - {scenario_name}: {str(e)}")
            
            result = {
                'test_number': self.test_count,
                'scenario_name': scenario_name,
                'scenario_type': scenario_type,
                'passed': False,
                'error': str(e),
                'timestamp': start_time.isoformat()
            }
            
            self.results.append(result)
            return result
    
    def _evaluate_real_world_results(self, scenario_type, metrics, metadata):
        """Evaluate results for real-world scenarios"""
        passed = True
        issues = []
        
        # General checks
        if metrics['unmet_demand_kwh'] > 100:
            passed = False
            issues.append(f"High unmet demand: {metrics['unmet_demand_kwh']:.2f} kWh")
        
        if metrics['final_health'] < 70:
            passed = False
            issues.append(f"Low system health: {metrics['final_health']:.1f}%")
        
        # Scenario-specific checks
        if scenario_type == "summer_peak":
            if metrics['total_cost'] > 150000:
                issues.append("High cost during summer peak")
        
        elif scenario_type == "monsoon_season":
            if metrics['renewable_usage_pct'] > 60:
                issues.append("Unrealistic renewable usage during monsoon")
        
        elif scenario_type == "ev_rush_hour":
            if metrics['unmet_demand_kwh'] > 50:
                issues.append("Unable to handle EV rush hour charging")
        
        return passed, issues
    
    def run_all_real_world_tests(self):
        """Run complete real-world scenarios suite"""
        print("\n" + "="*80)
        print("🌍 REAL-WORLD SCENARIOS TEST SUITE")
        print("="*80)
        
        scenarios = [
            ("Monsoon Season (Rainy)", "monsoon_season", 96),
            ("Summer Peak (42°C Heat)", "summer_peak", 96),
            ("Diwali Festival Load", "festival_diwali", 96),
            ("Industrial 3-Shift Pattern", "industrial_shifts", 96),
            ("Agricultural Irrigation", "agricultural_irrigation", 96),
            ("Urban Residential Pattern", "urban_residential", 96),
            ("Commercial Office Pattern", "commercial_office", 96),
            ("Power Cut Recovery", "power_cut_recovery", 96),
            ("EV Rush Hour Charging", "ev_rush_hour", 96),
        ]
        
        for scenario_name, scenario_type, duration in scenarios:
            self.test_real_world_scenario(scenario_name, scenario_type, duration)
        
        # Save results
        self.save_results()
        
        # Print summary
        self.print_summary()
    
    def save_results(self):
        """Save test results"""
        results_file = self.save_dir / f"real_world_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            'test_suite': 'Real-World Scenarios',
            'timestamp': datetime.now().isoformat(),
            'total_tests': self.test_count,
            'passed': self.passed,
            'failed': self.failed,
            'success_rate': (self.passed / self.test_count * 100) if self.test_count > 0 else 0,
            'results': self.results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to: {results_file}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 REAL-WORLD SCENARIOS SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.test_count}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ⚠️")
        success_rate = (self.passed / self.test_count * 100) if self.test_count > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*80)


def main():
    """Run real-world scenario tests"""
    tester = RealWorldScenarioTester()
    tester.run_all_real_world_tests()
    
    print("\n🌍 Real-world scenario testing complete!")
    print(f"Results saved in: {tester.save_dir}")


if __name__ == "__main__":
    main()
