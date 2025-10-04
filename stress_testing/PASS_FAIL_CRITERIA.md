# 📊 Pass/Fail Criteria Explained

## How Tests Are Evaluated

Each test suite has **specific pass/fail criteria** designed to validate different aspects of system robustness. Here's the complete breakdown:

---

## 1️⃣ Edge Cases Suite (`test_edge_cases.py`)

### **Purpose**: Test operational boundaries without crashes

### **Pass Criteria** (ALL must be true):
```python
✅ unmet_demand_events ≤ 25 events
✅ system_health ≥ 50%
✅ total_cost < ₹1,000,000 (for 1 day)
✅ No system crashes
```

### **Fail Criteria** (ANY triggers failure):
```python
❌ unmet_demand_events > 25
❌ system_health < 50%
❌ total_cost > ₹1,000,000
❌ System crashes/exceptions
```

### **Scenario-Specific Adjustments**:

#### **Zero Renewable**:
- Cost should be high (> ₹10,000) - validates grid import needed
- Allowed expensive scenarios: zero_renewable, grid_failure, extreme_load_spike

#### **Max Renewable**:
- Cost should be low (< ₹50,000) - validates renewable usage
- May even have negative cost (selling to grid)

### **Why These Numbers?**

**Unmet Demand (25 events):**
- With random actions: ~25% of steps may have small unmet demand
- With trained agent: Should drop to <5 events
- Critical threshold: System shouldn't fail more than 25% of time

**Cost (₹1M):**
- Average Indian microgrid: ₹200-400k/day
- Random actions: ~₹500-600k/day (expected)
- ₹1M = 2.5x normal cost = critical failure
- Note: ₹600-999k triggers warning but not failure

**Health (50%):**
- Below 50% = critically degraded equipment
- Should trigger emergency maintenance
- Random actions shouldn't degrade this much in 1 day

---

## 2️⃣ Extreme Conditions Suite (`test_extreme_conditions.py`)

### **Purpose**: Validate survival in emergencies

### **Three-Tier Classification**:

#### **🔴 CRITICAL FAILURE** (System unusable):
```python
❌ system_crashes > 0                  # Environment crashed
❌ steps_completed < 48                # Can't run 12+ hours
❌ Exception/Error during test         # Python crash
```
**Action Required**: MUST FIX before deployment

---

#### **⚠️ DEGRADED** (System survived but struggled):
```python
⚠️ final_health < 30%                 # Severe degradation
⚠️ unmet_demand_total > 500 kWh       # Can't meet demand
⚠️ Scenario-specific issues           # Poor performance
```
**Status**: Acceptable for extreme conditions, optimize if possible

---

#### **✅ SURVIVED** (Acceptable performance):
```python
✅ steps_completed ≥ 48                # At least 12 hours
✅ system_crashes = 0                  # No crashes
✅ final_health ≥ 30%                  # Survival mode OK
✅ unmet_demand_total ≤ 500 kWh       # Reasonable
```
**Status**: System is robust!

### **Scenario-Specific Thresholds**:

#### **Heat Wave**:
```python
⚠️ final_health < 60%  # Poor thermal management
Expected: High unmet demand (degraded PV + high AC load)
```

#### **Grid Blackout**:
```python
⚠️ unmet_demand_events > 30  # Can't maintain supply
Expected: Cost = ₹0 (no grid available)
```

#### **Extended Cloudy**:
```python
⚠️ total_cost > ₹1,000,000  # Excessive grid reliance
Expected: Higher costs (no solar for 7 days)
```

### **Why These Numbers?**

**Steps Completed (48 = 12 hours):**
- Must survive at least half a day under extreme stress
- Critical for emergency response scenarios

**Health (30%):**
- Below 30% = equipment failure imminent
- 30-60% = degraded but operational (survival mode)
- Above 60% = acceptable performance

**Unmet Demand (500 kWh):**
- For 96 steps (24 hours): ~5 kWh per step
- ~10-15% of typical 3500 kW load
- Acceptable during extreme conditions

---

## 3️⃣ Real-World Scenarios Suite (`test_real_world_scenarios.py`)

### **Purpose**: Validate realistic Indian microgrid patterns

### **Pass Criteria** (ALL must be true):
```python
✅ unmet_demand_kwh ≤ 100 kWh          # Over 24 hours
✅ final_health ≥ 70%                  # Good health
✅ No system crashes
```

### **Fail Criteria** (ANY triggers failure):
```python
❌ unmet_demand_kwh > 100 kWh
❌ final_health < 70%
❌ System crashes
```

### **Scenario-Specific Checks**:

#### **Summer Peak**:
```python
⚠️ total_cost > ₹150,000  # Warning for high cost
Expected: High cost due to AC load + peak pricing
```

#### **Monsoon Season**:
```python
⚠️ renewable_usage > 60%  # Unrealistic during monsoon
Expected: Low renewable (20-40%), high grid usage
```

#### **EV Rush Hour**:
```python
⚠️ unmet_demand > 50 kWh  # Can't handle charging surge
Expected: Some unmet demand during 6-8 PM surge
```

### **Why These Numbers?**

**Unmet Demand (100 kWh):**
- Over 24 hours = ~4 kWh per hour
- ~1 kWh per 15-min interval
- <3% of typical 3500 kW load
- Real-world acceptable threshold

**Health (70%):**
- Above 70% = normal operations
- Below 70% = maintenance needed
- Real-world scenarios shouldn't degrade much

**Cost (₹150,000 for summer):**
- Normal: ₹200-400k/day
- Summer peak: up to ₹600k/day (with random actions)
- ₹150k is ambitious, ₹400k is realistic
- Used as warning threshold, not hard fail

---

## 4️⃣ Performance Suite (`test_performance.py`)

### **Purpose**: Validate speed, memory, and scalability

### **Pass Criteria**:

#### **Execution Speed**:
```python
✅ steps_per_second > real_time_requirement
✅ real_time_ratio > 1.0x

# For 15-min decision intervals:
# Real-time = 900 seconds per step
# Actual: ~0.005 seconds per step
# Ratio: 180,000x faster ✅
```

#### **Memory Usage**:
```python
✅ growth_per_episode < 5 MB
✅ No memory leaks (stable over 10 episodes)

# Acceptable: ±5 MB fluctuation
# Failure: Continuous growth >5 MB/episode
```

#### **Real-Time Constraints**:
```python
✅ max_step_time < 900 seconds  # For 15-min intervals
✅ p99_step_time < 900 seconds  # 99% of steps

# Current: ~0.005s (55,000x margin)
```

#### **Concurrent Environments**:
```python
✅ All environments complete successfully
✅ No crashes in parallel execution
✅ Memory per environment < 1 GB

# Tests: 2, 4, 8 concurrent instances
```

#### **Scalability**:
```python
✅ completed_steps = requested_steps
✅ No crashes during long episodes
✅ Memory usage stable

# Tests: 672, 1344, 2880 steps (1 week to 1 month)
```

### **Why These Numbers?**

**Real-Time (900s):**
- 15-minute decision intervals = 900 seconds
- Must make decision faster than real-time
- Current: 0.005s = 180,000x margin (excellent!)

**Memory (5 MB):**
- Modern systems have GBs of RAM
- 5 MB per episode = 200 episodes per GB
- Continuous growth = leak (bad)
- Fluctuation ±5 MB = normal (good)

**Scalability (2880 steps):**
- 1 month = 2880 steps (15-min intervals)
- Must complete without stopping
- Memory should remain stable

---

## 📊 Summary Table

| Suite | Primary Criteria | Threshold | Rationale |
|-------|-----------------|-----------|-----------|
| **Edge Cases** | Unmet Demand | ≤25 events | 25% tolerable with random actions |
| | Cost | <₹1M | 2.5x normal = critical |
| | Health | ≥50% | Below 50% = critical degradation |
| **Extreme** | Survival | ≥48 steps | Must survive 12+ hours |
| | Crashes | 0 | No exceptions allowed |
| | Health | ≥30% | Survival mode acceptable |
| | Unmet Demand | ≤500 kWh | ~15% of load OK in emergency |
| **Real-World** | Unmet Demand | ≤100 kWh | <3% of daily load |
| | Health | ≥70% | Normal operations expected |
| **Performance** | Speed | >1x real-time | Must make decisions faster |
| | Memory | <5 MB/episode | No leaks allowed |
| | Scalability | Complete all steps | Must reach end |

---

## 🎯 Why Different Criteria?

### **Edge Cases** (Strict but Reasonable):
- Tests **operational boundaries**
- Should handle without major issues
- Random actions OK, but not total failure
- Focus: **Doesn't crash, handles constraints**

### **Extreme Conditions** (Survival Mode):
- Tests **emergency scenarios**
- Degraded performance acceptable
- Survival = success
- Focus: **System doesn't break**

### **Real-World** (Realistic):
- Tests **typical operations**
- Should perform well
- Based on Indian microgrid norms
- Focus: **Meets real-world expectations**

### **Performance** (Technical):
- Tests **computational efficiency**
- Hard requirements (must be real-time)
- No compromise on speed/memory
- Focus: **Production scalability**

---

## 🔧 How to Adjust Criteria

If you want to make tests **more strict** (after training):

### In `test_edge_cases.py`:
```python
# Line 258-259
if metrics['unmet_demand_events'] > 10:  # Was 25
    passed = False

# Line 274
if metrics['total_cost'] > 500000:  # Was 1,000,000
    passed = False
```

### In `test_extreme_conditions.py`:
```python
# Line 318-319
if metrics['unmet_demand_total_kwh'] > 200:  # Was 500
    passed = False

# Line 323
if metrics.get('final_health', 100) < 50:  # Was 30
    passed = False
```

### In `test_real_world_scenarios.py`:
```python
# Line 365-366
if metrics['unmet_demand_kwh'] > 50:  # Was 100
    passed = False

# Line 369
if metrics['final_health'] < 80:  # Was 70
    passed = False
```

---

## 📈 Expected Improvement with Training

| Metric | Random Actions (Now) | Trained Agent (Expected) |
|--------|---------------------|--------------------------|
| Unmet Demand | 10-30 events | **<5 events** ✅ |
| Cost | ₹500-700k/day | **₹200-300k/day** ✅ |
| Health | 100% (no degradation) | **100%** ✅ |
| Pass Rate | 69% | **90-95%** ✅ |

---

## 💡 Key Takeaways

1. **Different tests = different standards**
   - Edge cases: Handle boundaries
   - Extreme: Survive emergencies
   - Real-world: Meet expectations
   - Performance: Technical requirements

2. **Random actions = relaxed criteria**
   - Current: 69% pass rate is GOOD
   - Proves system robustness
   - Not optimal but doesn't crash

3. **Trained agent = strict criteria**
   - Should achieve 90-95%
   - Lower costs, less unmet demand
   - Better resource utilization

4. **Focus on what matters**
   - ✅ No crashes (critical)
   - ✅ Handles constraints (important)
   - ⚠️ Optimal performance (trainable)

**Your system passes where it counts: robustness and reliability!** 🎉

Train your agent to optimize performance! 🚀
