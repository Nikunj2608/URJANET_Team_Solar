"""
Quick Start Script for Stress Testing
Run this to quickly test the system
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       MICROGRID EMS STRESS TESTING                            ║
║                          Quick Start Script                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝

This script will run a quick subset of tests to verify your system.
For comprehensive testing, use: python run_all_tests.py

""")

import time
from datetime import datetime
from pathlib import Path

# Import testers
from test_edge_cases import EdgeCaseTester
from test_real_world_scenarios import RealWorldScenarioTester

def quick_test():
    """Run quick validation tests"""
    start_time = datetime.now()
    
    print("🚀 Starting Quick Stress Test...\n")
    
    # Test 1: A few edge cases
    print("="*80)
    print("QUICK TEST 1: Edge Cases")
    print("="*80)
    
    try:
        edge_tester = EdgeCaseTester(save_dir="results/quick_test")
        
        # Run just 3 edge cases
        edge_tester.test_scenario(
            "Zero Renewable Generation",
            "zero_renewable",
            duration_steps=96
        )
        
        edge_tester.test_scenario(
            "Extreme Load Spike",
            "extreme_load_spike",
            duration_steps=96
        )
        
        edge_tester.test_scenario(
            "Grid Failure",
            "grid_failure",
            duration_steps=96
        )
        
        edge_tester.save_results()
        
        print(f"\n✅ Edge Cases: {edge_tester.passed}/{edge_tester.test_count} passed")
        
    except Exception as e:
        print(f"❌ Edge Cases failed: {str(e)}")
    
    # Test 2: Real-world scenario
    print("\n\n" + "="*80)
    print("QUICK TEST 2: Real-World Scenario")
    print("="*80)
    
    try:
        rw_tester = RealWorldScenarioTester(save_dir="results/quick_test")
        
        # Run 2 real-world scenarios
        rw_tester.test_real_world_scenario(
            "Summer Peak Load",
            "summer_peak",
            duration_steps=96
        )
        
        rw_tester.test_real_world_scenario(
            "Urban Residential Pattern",
            "urban_residential",
            duration_steps=96
        )
        
        rw_tester.save_results()
        
        print(f"\n✅ Real-World: {rw_tester.passed}/{rw_tester.test_count} passed")
        
    except Exception as e:
        print(f"❌ Real-World tests failed: {str(e)}")
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n\n" + "="*80)
    print("📊 QUICK TEST SUMMARY")
    print("="*80)
    print(f"Duration: {duration:.1f}s")
    print(f"Start: {start_time.strftime('%H:%M:%S')}")
    print(f"End: {end_time.strftime('%H:%M:%S')}")
    
    total_tests = edge_tester.test_count + rw_tester.test_count
    total_passed = edge_tester.passed + rw_tester.passed
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {total_passed} ✅")
    print(f"Failed: {total_tests - total_passed} ⚠️")
    
    if total_passed == total_tests:
        print("\n🎉 ALL QUICK TESTS PASSED! System looks good.")
    else:
        print(f"\n⚠️  Some tests failed. Review results in stress_testing/results/quick_test/")
    
    print("\n💡 To run comprehensive tests: python run_all_tests.py")
    print("="*80)


if __name__ == "__main__":
    try:
        quick_test()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Quick test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
