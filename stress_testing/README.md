# 🔬 Comprehensive Stress Testing & Validation Suite

## Overview

This testing suite provides **extensive stress testing** for the complete RL-based EMS with integrated anomaly detection system. It simulates real-world conditions, edge cases, and extreme scenarios to validate system robustness.

## ✅ Available Test Suites (29 Tests)

### 1. **Edge Cases** (`test_edge_cases.py`) - 7 Tests ✅
Tests system behavior at operational boundaries:
- ✅ Zero renewable generation (night/cloudy)
- ✅ Maximum renewable generation (full capacity)
- ✅ Extreme load spikes (sudden demand surges)
- ✅ Grid failures (complete unavailability)
- ✅ Rapid weather changes (solar fluctuations)
- ✅ Price volatility (wildly fluctuating prices)
- ✅ Battery stress cycling (high charge/discharge)

### 2. **Extreme Conditions** (`test_extreme_conditions.py`) - 8 Tests ✅
Tests under severe and emergency scenarios:
- 🔥 Heat waves (45°C+ ambient temperature)
- 🌧️ Extended cloudy period (7+ days monsoon)
- ⚠️ Equipment cascading failures
- 🚨 Multiple simultaneous anomalies
- 🔋 Battery thermal runaway scenario
- ⚡ Complete grid blackout (extended)
- 🔌 Sensor failures and bad data
- 🛡️ Cyber attack simulation

### 3. **Real-World Scenarios** (`test_real_world_scenarios.py`) - 9 Tests ✅
Tests with authentic Indian microgrid patterns:
- 🌧️ Monsoon season (June-Sep, low solar)
- ☀️ Summer peak (April-May, 42°C, high AC)
- 🪔 Diwali festival load (evening decorative spike)
- 🏭 Industrial 3-shift pattern (manufacturing)
- 🚜 Agricultural irrigation (pump loads)
- 🏘️ Urban residential (morning/evening peaks)
- 🏢 Commercial office (9 AM - 6 PM heavy)
- 🔌 Power cut recovery (outage & restoration)
- 🚗 EV rush hour charging (evening surge)

### 4. **Performance Tests** (`test_performance.py`) - 5 Tests ✅
Tests speed, memory, and scalability:
- ⚡ Execution speed benchmarks (1-7 days)
- 💾 Memory usage & leak detection
- 📈 Scalability (up to 1 month episodes)
- 🔄 Concurrent environment instances (2-8 parallel)
- ⏱️ Real-time constraints (15-min intervals)

### 5. **Integration Tests** (Coming Soon)
- RL agent + Anomaly detection coordination
- API response times
- WebSocket stability

### 6. **Anomaly Detection Stress Tests** (Coming Soon)
- False positive rates
- Detection accuracy under load
- Response time under load
- Multi-anomaly scenarios

## 🚀 Quick Start

### Option 1: Quick Validation (2-5 minutes) ⚡
Perfect for rapid testing during development:
```bash
cd stress_testing
python quick_start.py
```
Runs 5 essential tests.

### Option 2: Full Test Suite (15-45 minutes) 🎯
Comprehensive testing before deployment:
```bash
python run_all_tests.py
```
Runs all 29 tests across 4 suites.

### Option 3: Skip Performance (10-25 minutes) 🏃
```bash
python run_all_tests.py --skip-performance
```

### Option 4: Individual Test Suites 🔍
```bash
python test_edge_cases.py              # 3-5 min
python test_extreme_conditions.py      # 8-12 min
python test_real_world_scenarios.py    # 10-15 min
python test_performance.py             # 5-10 min
```

## 📊 Test Results

Results saved in `results/` with timestamps:
```
results/
├── quick_test/                        # Quick validation results
├── edge_cases/
│   └── edge_cases_20250104_143022.json
├── extreme_conditions/
│   └── extreme_conditions_20250104_144515.json
├── real_world/
│   └── real_world_20250104_150822.json
├── performance/
│   └── performance_20250104_152130.json
└── master/
    └── test_summary_20250104_153045.json
```

Each JSON file contains:
- Test metadata and timing
- Individual test results
- Metrics (cost, emissions, health, anomalies)
- Pass/fail status and issues

## ✅ Pass Criteria

### Edge Cases
- ✓ No system crashes
- ✓ Unmet demand < 100 kWh
- ✓ System health > 70%
- ✓ All 96 steps completed

### Extreme Conditions
- ✓ System survives (no crashes)
- ✓ Health > 30% (survival mode)
- ✓ Critical alerts generated
- ✓ Completes ≥ 48 steps (12 hours)

### Real-World Scenarios
- ✓ Unmet demand < 100 kWh
- ✓ Health > 70%
- ✓ Cost < ₹150,000/day
- ✓ Appropriate anomaly detection

### Performance
- ✓ Real-time capable (< 900s/step)
- ✓ Memory growth < 5MB/episode
- ✓ Concurrent instances supported
- ✓ Scales to 1-week+ episodes

## 📈 Success Rate Grades

- **🌟 A+ (95%+)**: EXCELLENT - Production-ready
- **✨ A (90-95%)**: VERY GOOD - Minor issues
- **👍 B (80-90%)**: GOOD - Some issues
- **⚠️ C (70-80%)**: ACCEPTABLE - Needs improvement
- **🔧 D (<70%)**: NEEDS WORK - Not ready

## Test Matrix

| Test Suite | Tests | Duration | Status |
|------------|-------|----------|--------|
| Edge Cases | 7 | 3-5 min | ✅ Ready |
| Extreme Conditions | 8 | 8-12 min | ✅ Ready |
| Real-World Scenarios | 9 | 10-15 min | ✅ Ready |
| Performance | 5 | 5-10 min | ✅ Ready |
| Integration | TBD | TBD | 🔄 Coming Soon |
| Anomaly Stress | TBD | TBD | 🔄 Coming Soon |
| **TOTAL** | **29** | **26-42 min** | - |

## 🏗️ Directory Structure

```
stress_testing/
├── README.md                          # This file
├── quick_start.py                     # Quick validation ⚡
├── run_all_tests.py                   # Master runner 🎯
├── test_edge_cases.py                 # 7 edge case tests
├── test_extreme_conditions.py         # 8 emergency tests
├── test_real_world_scenarios.py       # 9 Indian patterns
├── test_performance.py                # 5 performance tests
└── results/                           # Auto-created
```

## 🎯 Recommended Workflow

**During Development**: `python quick_start.py`  
**Before Commit**: `python test_edge_cases.py`  
**Before Deploy**: `python run_all_tests.py`  
**Performance Tuning**: `python test_performance.py`  
**Production Validation**: Run real-world + extreme

## Requirements

All standard requirements + stress testing tools (auto-installed).

---

**Ready to stress test your system!** 🔬💪
