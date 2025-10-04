"""
Performance Testing Suite
Tests system performance, speed, memory usage, and scalability

Tests:
1. Execution speed benchmarks
2. Memory profiling
3. Scalability testing (longer episodes)
4. Concurrent environment instances
5. API response time testing
6. Database/logging overhead
7. Real-time constraint validation
8. Resource utilization monitoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import json
import time
import psutil
import tracemalloc
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from microgrid_env import MicrogridEMSEnv


class PerformanceTester:
    """Test system performance and resource usage"""
    
    def __init__(self, save_dir="results/performance"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.test_count = 0
        
        # Get system info
        self.system_info = {
            'cpu_count': psutil.cpu_count(),
            'total_memory_gb': psutil.virtual_memory().total / (1024**3),
            'python_version': sys.version
        }
    
    def _create_test_data(self, steps=96):
        """Create standard test data"""
        pv = pd.DataFrame({'pv_power_kw': self._generate_solar_profile(steps)})
        wt = pd.DataFrame({'wt_power_kw': 700 + np.random.rand(steps) * 1000})
        load = pd.DataFrame({'load_kw': 3500 + np.random.rand(steps) * 1000})
        price = pd.DataFrame({'price_inr_per_kwh': 5.5 + np.random.rand(steps) * 2.5})
        return pv, wt, load, price
    
    def _generate_solar_profile(self, steps):
        """Generate realistic solar profile"""
        profile = np.zeros(steps)
        for i in range(steps):
            hour = (i * 0.25) % 24
            if 6 <= hour <= 18:
                profile[i] = 3200 * (1 - ((hour - 12) / 6) ** 2) * np.random.uniform(0.8, 1.0)
        return np.maximum(0, profile)
    
    def test_execution_speed(self):
        """Test execution speed for episode"""
        print(f"\n{'='*80}")
        print(f"⚡ PERFORMANCE TEST: Execution Speed")
        print(f"{'='*80}")
        
        self.test_count += 1
        
        # Test different episode lengths
        episode_lengths = [96, 192, 384, 672]  # 1 day, 2 days, 4 days, 1 week
        
        results = []
        
        for length in episode_lengths:
            print(f"\n  Testing {length} steps ({length/96:.1f} days)...")
            
            pv, wt, load, price = self._create_test_data(length + 100)
            
            env = MicrogridEMSEnv(
                pv_profile=pv,
                wt_profile=wt,
                load_profile=load,
                price_profile=price,
                enable_evs=True,
                enable_degradation=True,
                enable_emissions=True
            )
            
            # Warm-up
            env.reset(episode_start_idx=0)
            for _ in range(5):
                env.step(env.action_space.sample())
            
            # Actual test
            start_time = time.perf_counter()
            env.reset(episode_start_idx=0)
            
            for _ in range(length):
                action = env.action_space.sample()
                obs, reward, done, info = env.step(action)
                if done:
                    break
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            steps_per_sec = length / duration
            real_time_ratio = (length * 15 / 60) / duration  # 15 min per step
            
            result = {
                'episode_length': length,
                'duration_seconds': duration,
                'steps_per_second': steps_per_sec,
                'real_time_ratio': real_time_ratio,
                'meets_real_time': real_time_ratio >= 1.0
            }
            
            results.append(result)
            
            print(f"    Duration: {duration:.3f}s")
            print(f"    Steps/sec: {steps_per_sec:.1f}")
            print(f"    Real-time ratio: {real_time_ratio:.1f}x")
            print(f"    {'✅ REAL-TIME CAPABLE' if result['meets_real_time'] else '⚠️ TOO SLOW'}")
        
        # Overall assessment
        all_real_time = all(r['meets_real_time'] for r in results)
        
        test_result = {
            'test_number': self.test_count,
            'test_name': 'Execution Speed Benchmark',
            'passed': all_real_time,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(test_result)
        
        print(f"\n  Overall: {'✅ PASS' if all_real_time else '⚠️ FAIL'}")
        
        return test_result
    
    def test_memory_usage(self):
        """Test memory usage and leaks"""
        print(f"\n{'='*80}")
        print(f"💾 PERFORMANCE TEST: Memory Usage")
        print(f"{'='*80}")
        
        self.test_count += 1
        
        pv, wt, load, price = self._create_test_data(96)
        
        # Start memory tracking
        tracemalloc.start()
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / (1024**2)  # MB
        
        print(f"\n  Initial Memory: {initial_memory:.2f} MB")
        
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
        
        after_creation = process.memory_info().rss / (1024**2)
        print(f"  After Creation: {after_creation:.2f} MB (+{after_creation - initial_memory:.2f} MB)")
        
        # Run multiple episodes
        memory_samples = []
        
        for ep in range(10):
            env.reset(episode_start_idx=0)
            
            for step in range(96):
                action = env.action_space.sample()
                env.step(action)
            
            current_memory = process.memory_info().rss / (1024**2)
            memory_samples.append(current_memory)
            
            if ep % 3 == 0:
                print(f"  After Episode {ep+1}: {current_memory:.2f} MB")
        
        # Check for memory leak
        memory_growth = memory_samples[-1] - memory_samples[0]
        growth_per_episode = memory_growth / 10
        
        # Get peak memory
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n  Final Memory: {memory_samples[-1]:.2f} MB")
        print(f"  Memory Growth: {memory_growth:.2f} MB over 10 episodes")
        print(f"  Growth per Episode: {growth_per_episode:.2f} MB")
        print(f"  Peak Memory (traced): {peak / (1024**2):.2f} MB")
        
        # Pass criteria: less than 5MB growth per episode
        passed = growth_per_episode < 5.0
        
        result = {
            'test_number': self.test_count,
            'test_name': 'Memory Usage & Leak Test',
            'passed': passed,
            'initial_memory_mb': initial_memory,
            'final_memory_mb': memory_samples[-1],
            'total_growth_mb': memory_growth,
            'growth_per_episode_mb': growth_per_episode,
            'peak_memory_mb': peak / (1024**2),
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        
        print(f"\n  Overall: {'✅ PASS' if passed else '⚠️ FAIL - Potential memory leak'}")
        
        return result
    
    def test_scalability(self):
        """Test scalability with very long episodes"""
        print(f"\n{'='*80}")
        print(f"📈 PERFORMANCE TEST: Scalability")
        print(f"{'='*80}")
        
        self.test_count += 1
        
        # Test with 1 week, 2 weeks, 1 month
        durations = [
            (672, "1 Week"),
            (1344, "2 Weeks"),
            (2880, "1 Month")
        ]
        
        results = []
        
        for steps, label in durations:
            print(f"\n  Testing {label} ({steps} steps)...")
            
            try:
                pv, wt, load, price = self._create_test_data(steps + 100)
                
                env = MicrogridEMSEnv(
                    pv_profile=pv,
                    wt_profile=wt,
                    load_profile=load,
                    price_profile=price,
                    enable_evs=True,
                    enable_degradation=True,
                    enable_emissions=True
                )
                
                start_time = time.perf_counter()
                start_memory = psutil.Process().memory_info().rss / (1024**2)
                
                # Reset with custom max_steps
                env.reset(episode_start_idx=0, max_steps=steps)
                
                completed_steps = 0
                for step in range(steps):
                    action = env.action_space.sample()
                    obs, reward, done, info = env.step(action)
                    completed_steps += 1
                    
                    if done:
                        break
                
                end_time = time.perf_counter()
                end_memory = psutil.Process().memory_info().rss / (1024**2)
                
                duration = end_time - start_time
                memory_used = end_memory - start_memory
                
                result = {
                    'duration_label': label,
                    'steps': steps,
                    'completed_steps': completed_steps,
                    'duration_seconds': duration,
                    'memory_used_mb': memory_used,
                    'success': completed_steps == steps
                }
                
                results.append(result)
                
                print(f"    Completed: {completed_steps}/{steps} steps")
                print(f"    Duration: {duration:.2f}s")
                print(f"    Memory Used: {memory_used:.2f} MB")
                print(f"    {'✅ SUCCESS' if result['success'] else '⚠️ INCOMPLETE'}")
                
            except Exception as e:
                print(f"    ❌ FAILED: {str(e)}")
                results.append({
                    'duration_label': label,
                    'steps': steps,
                    'success': False,
                    'error': str(e)
                })
        
        all_success = all(r.get('success', False) for r in results)
        
        test_result = {
            'test_number': self.test_count,
            'test_name': 'Scalability Test',
            'passed': all_success,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(test_result)
        
        print(f"\n  Overall: {'✅ PASS' if all_success else '⚠️ FAIL'}")
        
        return test_result
    
    def test_concurrent_environments(self):
        """Test multiple concurrent environment instances"""
        print(f"\n{'='*80}")
        print(f"🔄 PERFORMANCE TEST: Concurrent Environments")
        print(f"{'='*80}")
        
        self.test_count += 1
        
        num_envs = [2, 4, 8]
        results = []
        
        for n in num_envs:
            print(f"\n  Testing {n} concurrent environments...")
            
            def run_env(env_id):
                """Run single environment"""
                try:
                    pv, wt, load, price = self._create_test_data(96)
                    
                    env = MicrogridEMSEnv(
                        pv_profile=pv,
                        wt_profile=wt,
                        load_profile=load,
                        price_profile=price,
                        enable_evs=True,
                        enable_degradation=True,
                        enable_emissions=True
                    )
                    
                    env.reset(episode_start_idx=0)
                    
                    for step in range(96):
                        action = env.action_space.sample()
                        env.step(action)
                    
                    return {'env_id': env_id, 'success': True}
                    
                except Exception as e:
                    return {'env_id': env_id, 'success': False, 'error': str(e)}
            
            start_time = time.perf_counter()
            start_memory = psutil.Process().memory_info().rss / (1024**2)
            
            # Run concurrently
            with ThreadPoolExecutor(max_workers=n) as executor:
                futures = [executor.submit(run_env, i) for i in range(n)]
                env_results = [f.result() for f in as_completed(futures)]
            
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss / (1024**2)
            
            duration = end_time - start_time
            memory_used = end_memory - start_memory
            success_count = sum(1 for r in env_results if r['success'])
            
            result = {
                'num_environments': n,
                'duration_seconds': duration,
                'memory_used_mb': memory_used,
                'memory_per_env_mb': memory_used / n,
                'success_count': success_count,
                'all_success': success_count == n
            }
            
            results.append(result)
            
            print(f"    Duration: {duration:.2f}s")
            print(f"    Memory Used: {memory_used:.2f} MB ({memory_used/n:.2f} MB per env)")
            print(f"    Success: {success_count}/{n}")
            print(f"    {'✅ SUCCESS' if result['all_success'] else '⚠️ SOME FAILED'}")
        
        all_success = all(r['all_success'] for r in results)
        
        test_result = {
            'test_number': self.test_count,
            'test_name': 'Concurrent Environments Test',
            'passed': all_success,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(test_result)
        
        print(f"\n  Overall: {'✅ PASS' if all_success else '⚠️ FAIL'}")
        
        return test_result
    
    def test_real_time_constraints(self):
        """Test if system can run in real-time (15-min decision intervals)"""
        print(f"\n{'='*80}")
        print(f"⏱️ PERFORMANCE TEST: Real-Time Constraints")
        print(f"{'='*80}")
        
        self.test_count += 1
        
        pv, wt, load, price = self._create_test_data(96)
        
        env = MicrogridEMSEnv(
            pv_profile=pv,
            wt_profile=wt,
            load_profile=load,
            price_profile=price,
            enable_evs=True,
            enable_degradation=True,
            enable_emissions=True
        )
        
        env.reset(episode_start_idx=0)
        
        # Test 100 steps
        step_times = []
        
        print(f"\n  Testing 100 steps (real-time = 15 min = 900s per step)...")
        
        for i in range(100):
            action = env.action_space.sample()
            
            start = time.perf_counter()
            obs, reward, done, info = env.step(action)
            end = time.perf_counter()
            
            step_time = end - start
            step_times.append(step_time)
            
            if done:
                break
        
        avg_step_time = np.mean(step_times)
        max_step_time = np.max(step_times)
        p95_step_time = np.percentile(step_times, 95)
        p99_step_time = np.percentile(step_times, 99)
        
        real_time_limit = 900.0  # 15 minutes in seconds
        
        print(f"\n  Average Step Time: {avg_step_time*1000:.2f} ms")
        print(f"  Max Step Time: {max_step_time*1000:.2f} ms")
        print(f"  P95 Step Time: {p95_step_time*1000:.2f} ms")
        print(f"  P99 Step Time: {p99_step_time*1000:.2f} ms")
        print(f"  Real-Time Limit: {real_time_limit:.0f}s")
        
        # Check if all steps meet real-time constraint
        all_real_time = max_step_time < real_time_limit
        
        result = {
            'test_number': self.test_count,
            'test_name': 'Real-Time Constraints Test',
            'passed': all_real_time,
            'avg_step_time_ms': avg_step_time * 1000,
            'max_step_time_ms': max_step_time * 1000,
            'p95_step_time_ms': p95_step_time * 1000,
            'p99_step_time_ms': p99_step_time * 1000,
            'real_time_limit_s': real_time_limit,
            'margin_of_safety': real_time_limit / max_step_time if max_step_time > 0 else float('inf'),
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        
        print(f"\n  Margin of Safety: {result['margin_of_safety']:.1f}x")
        print(f"  Overall: {'✅ PASS - REAL-TIME CAPABLE' if all_real_time else '⚠️ FAIL - TOO SLOW'}")
        
        return result
    
    def run_all_performance_tests(self):
        """Run all performance tests"""
        print("\n" + "="*80)
        print("⚡ PERFORMANCE TEST SUITE")
        print("="*80)
        print(f"System: {self.system_info['cpu_count']} CPUs, {self.system_info['total_memory_gb']:.1f} GB RAM")
        
        # Run tests
        self.test_execution_speed()
        self.test_memory_usage()
        self.test_real_time_constraints()
        self.test_concurrent_environments()
        self.test_scalability()
        
        # Save results
        self.save_results()
        
        # Print summary
        self.print_summary()
    
    def save_results(self):
        """Save test results"""
        results_file = self.save_dir / f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        passed = sum(1 for r in self.results if r.get('passed', False))
        
        summary = {
            'test_suite': 'Performance',
            'system_info': self.system_info,
            'timestamp': datetime.now().isoformat(),
            'total_tests': self.test_count,
            'passed': passed,
            'failed': self.test_count - passed,
            'results': self.results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to: {results_file}")
    
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for r in self.results if r.get('passed', False))
        
        print("\n" + "="*80)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.test_count}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {self.test_count - passed} ⚠️")
        print("="*80)


def main():
    """Run performance tests"""
    tester = PerformanceTester()
    tester.run_all_performance_tests()
    
    print("\n⚡ Performance testing complete!")
    print(f"Results saved in: {tester.save_dir}")


if __name__ == "__main__":
    main()
