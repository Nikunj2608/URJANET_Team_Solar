"""
Master Test Runner
Orchestrates all stress testing suites and generates comprehensive reports

Test Suites:
1. Edge Cases
2. Extreme Conditions  
3. Real-World Scenarios
4. Performance
5. (Future: Integration, Anomaly Detection Stress)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import time
from datetime import datetime
from pathlib import Path

# Import all test suites
from test_edge_cases import EdgeCaseTester
from test_extreme_conditions import ExtremeConditionsTester
from test_real_world_scenarios import RealWorldScenarioTester
from test_performance import PerformanceTester


class MasterTestRunner:
    """Orchestrate all stress testing suites"""
    
    def __init__(self, output_dir="results/master"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.start_time = None
        self.end_time = None
        self.suite_results = {}
        
    def run_all_tests(self, skip_performance=False):
        """Run all test suites"""
        print("\n" + "="*80)
        print("🚀 MASTER STRESS TEST SUITE")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        self.start_time = datetime.now()
        
        # Suite 1: Edge Cases
        print("\n\n" + "🎯 " + "="*75)
        print("SUITE 1: EDGE CASES")
        print("="*80)
        
        try:
            edge_tester = EdgeCaseTester(save_dir="results/edge_cases")
            edge_tester.run_all_edge_cases()
            
            self.suite_results['edge_cases'] = {
                'status': 'completed',
                'total_tests': edge_tester.test_count,
                'passed': edge_tester.passed,
                'failed': edge_tester.failed,
                'results_dir': str(edge_tester.save_dir)
            }
        except Exception as e:
            print(f"❌ Edge Cases suite failed: {str(e)}")
            self.suite_results['edge_cases'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Suite 2: Extreme Conditions
        print("\n\n" + "🔥 " + "="*75)
        print("SUITE 2: EXTREME CONDITIONS")
        print("="*80)
        
        try:
            extreme_tester = ExtremeConditionsTester(save_dir="results/extreme_conditions")
            extreme_tester.run_all_extreme_tests()
            
            self.suite_results['extreme_conditions'] = {
                'status': 'completed',
                'total_tests': extreme_tester.test_count,
                'passed': extreme_tester.passed,
                'failed': extreme_tester.failed,
                'critical_failures': extreme_tester.critical_failures,
                'results_dir': str(extreme_tester.save_dir)
            }
        except Exception as e:
            print(f"❌ Extreme Conditions suite failed: {str(e)}")
            self.suite_results['extreme_conditions'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Suite 3: Real-World Scenarios
        print("\n\n" + "🌍 " + "="*75)
        print("SUITE 3: REAL-WORLD SCENARIOS")
        print("="*80)
        
        try:
            real_world_tester = RealWorldScenarioTester(save_dir="results/real_world")
            real_world_tester.run_all_real_world_tests()
            
            self.suite_results['real_world_scenarios'] = {
                'status': 'completed',
                'total_tests': real_world_tester.test_count,
                'passed': real_world_tester.passed,
                'failed': real_world_tester.failed,
                'results_dir': str(real_world_tester.save_dir)
            }
        except Exception as e:
            print(f"❌ Real-World Scenarios suite failed: {str(e)}")
            self.suite_results['real_world_scenarios'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Suite 4: Performance (optional - can be time consuming)
        if not skip_performance:
            print("\n\n" + "⚡ " + "="*75)
            print("SUITE 4: PERFORMANCE")
            print("="*80)
            
            try:
                perf_tester = PerformanceTester(save_dir="results/performance")
                perf_tester.run_all_performance_tests()
                
                self.suite_results['performance'] = {
                    'status': 'completed',
                    'total_tests': perf_tester.test_count,
                    'passed': sum(1 for r in perf_tester.results if r.get('passed', False)),
                    'failed': perf_tester.test_count - sum(1 for r in perf_tester.results if r.get('passed', False)),
                    'results_dir': str(perf_tester.save_dir)
                }
            except Exception as e:
                print(f"❌ Performance suite failed: {str(e)}")
                self.suite_results['performance'] = {
                    'status': 'failed',
                    'error': str(e)
                }
        else:
            print("\n\n⏭️  Skipping Performance suite (use --performance to include)")
            self.suite_results['performance'] = {
                'status': 'skipped'
            }
        
        self.end_time = datetime.now()
        
        # Generate summary
        self.generate_summary()
        
        # Print final report
        self.print_final_report()
    
    def generate_summary(self):
        """Generate comprehensive summary"""
        duration = (self.end_time - self.start_time).total_seconds()
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_critical = 0
        
        for suite_name, suite_data in self.suite_results.items():
            if suite_data['status'] == 'completed':
                total_tests += suite_data.get('total_tests', 0)
                total_passed += suite_data.get('passed', 0)
                total_failed += suite_data.get('failed', 0)
                total_critical += suite_data.get('critical_failures', 0)
        
        summary = {
            'test_run': {
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration_seconds': duration,
                'duration_formatted': self._format_duration(duration)
            },
            'overall_statistics': {
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_critical_failures': total_critical,
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            'suite_results': self.suite_results
        }
        
        # Save summary
        summary_file = self.output_dir / f"test_summary_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✓ Master summary saved to: {summary_file}")
        
        return summary
    
    def _format_duration(self, seconds):
        """Format duration in human-readable form"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    def print_final_report(self):
        """Print comprehensive final report"""
        print("\n\n" + "="*80)
        print("📊 FINAL STRESS TEST REPORT")
        print("="*80)
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        print(f"\nTest Duration: {self._format_duration(duration)}")
        print(f"Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End:   {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "-"*80)
        print("SUITE BREAKDOWN:")
        print("-"*80)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_critical = 0
        
        for suite_name, suite_data in self.suite_results.items():
            status = suite_data['status']
            
            suite_display = suite_name.replace('_', ' ').title()
            
            if status == 'completed':
                tests = suite_data.get('total_tests', 0)
                passed = suite_data.get('passed', 0)
                failed = suite_data.get('failed', 0)
                critical = suite_data.get('critical_failures', 0)
                
                total_tests += tests
                total_passed += passed
                total_failed += failed
                total_critical += critical
                
                success_rate = (passed / tests * 100) if tests > 0 else 0
                
                print(f"\n{suite_display}:")
                print(f"  Total Tests: {tests}")
                print(f"  Passed: {passed} ✅")
                print(f"  Failed: {failed} ⚠️")
                if critical > 0:
                    print(f"  Critical: {critical} 🔴")
                print(f"  Success Rate: {success_rate:.1f}%")
                
            elif status == 'failed':
                print(f"\n{suite_display}: ❌ FAILED")
                print(f"  Error: {suite_data.get('error', 'Unknown error')}")
                
            elif status == 'skipped':
                print(f"\n{suite_display}: ⏭️  SKIPPED")
        
        print("\n" + "-"*80)
        print("OVERALL STATISTICS:")
        print("-"*80)
        print(f"Total Tests Run: {total_tests}")
        print(f"Total Passed: {total_passed} ✅")
        print(f"Total Failed: {total_failed} ⚠️")
        if total_critical > 0:
            print(f"Critical Failures: {total_critical} 🔴")
        
        if total_tests > 0:
            overall_success = (total_passed / total_tests * 100)
            print(f"\nOverall Success Rate: {overall_success:.1f}%")
            
            # Grade the system
            if overall_success >= 95:
                grade = "A+ (EXCELLENT)"
                emoji = "🌟"
            elif overall_success >= 90:
                grade = "A (VERY GOOD)"
                emoji = "✨"
            elif overall_success >= 80:
                grade = "B (GOOD)"
                emoji = "👍"
            elif overall_success >= 70:
                grade = "C (ACCEPTABLE)"
                emoji = "⚠️"
            else:
                grade = "D (NEEDS WORK)"
                emoji = "🔧"
            
            print(f"\nSystem Grade: {grade} {emoji}")
        
        print("\n" + "="*80)
        print("Results saved in: stress_testing/results/")
        print("="*80)
        
        # Recommendations
        print("\n📋 RECOMMENDATIONS:")
        
        if total_critical > 0:
            print("  🔴 CRITICAL: Address critical failures immediately!")
        
        if total_failed > total_tests * 0.2:
            print("  ⚠️  WARNING: High failure rate. Review failed tests.")
        
        if total_passed == total_tests:
            print("  ✅ EXCELLENT: All tests passed! System is robust.")
        elif total_failed <= total_tests * 0.1:
            print("  👍 GOOD: Most tests passed. Minor issues to address.")
        
        print("\n" + "="*80)


def main():
    """Run master test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive stress tests')
    parser.add_argument('--skip-performance', action='store_true',
                       help='Skip performance tests (saves time)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests only')
    
    args = parser.parse_args()
    
    runner = MasterTestRunner()
    runner.run_all_tests(skip_performance=args.skip_performance or args.quick)
    
    print("\n✅ Master stress testing complete!")


if __name__ == "__main__":
    main()
