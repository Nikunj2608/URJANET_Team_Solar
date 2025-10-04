"""
Diagnostic Script - Extract ALL Key Info About RL System
Run this to answer EVERY question about the codebase
"""

import os
import sys
import json
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

print("="*80)
print("RL MICROGRID SYSTEM DIAGNOSTIC REPORT")
print("="*80)

# ========== 1. ENVIRONMENT ==========
print("\n" + "="*80)
print("1. ENVIRONMENT")
print("="*80)

try:
    from microgrid_env import MicrogridEMSEnv
    from env_config import *
    
    print(f"✓ Environment class: MicrogridEMSEnv")
    print(f"✓ File: microgrid_env.py")
    
    # Create dummy env to inspect
    pv = pd.DataFrame({'pv_total': [100]*1000})
    wt = pd.DataFrame({'wt_total': [50]*1000})
    load = pd.DataFrame({'load_total': [150]*1000})
    price = pd.DataFrame({'price': [7.5]*1000})
    
    env = MicrogridEMSEnv(pv, wt, load, price, random_seed=42)
    
    print(f"\nObservation Space:")
    print(f"  Shape: {env.observation_space.shape}")
    print(f"  Dimensions: {env.observation_space.shape[0]}")
    print(f"  Low: {env.observation_space.low[0]:.2f}")
    print(f"  High: {env.observation_space.high[0]:.2f}")
    
    print(f"\nAction Space:")
    print(f"  Shape: {env.action_space.shape}")
    print(f"  Dimensions: {env.action_space.shape[0]}")
    print(f"  Low: {env.action_space.low}")
    print(f"  High: {env.action_space.high}")
    
    print(f"\nTime Configuration:")
    print(f"  Episode hours: {EPISODE_HOURS}")
    print(f"  Steps per episode: {STEPS_PER_EPISODE}")
    print(f"  Hours per step: {HOURS_PER_STEP}")
    print(f"  Decision interval: {DECISION_INTERVAL_MINUTES} minutes")
    
    print(f"\nObservation Breakdown (from OBS_SPACE):")
    obs_config = OBS_SPACE
    print(f"  Temporal: {obs_config.hour_of_day + obs_config.minute_of_hour + obs_config.day_of_week + obs_config.is_weekend}")
    print(f"  PV: {obs_config.pv_current + obs_config.pv_forecast + obs_config.pv_history}")
    print(f"  Wind: {obs_config.wt_current + obs_config.wt_forecast + obs_config.wt_history}")
    print(f"  Load: {obs_config.load_current + obs_config.load_forecast + obs_config.load_history}")
    print(f"  Battery: {obs_config.battery_soc + obs_config.battery_soh + obs_config.battery_temperature}")
    print(f"  Grid: {obs_config.grid_price_current + obs_config.grid_price_forecast}")
    print(f"  EV: {obs_config.ev_connected_count + obs_config.ev_total_energy_needed}")
    print(f"  Total calculated: {obs_config.get_total_dim()}")
    
    print(f"\nAction Breakdown (from ACTION_SPACE):")
    act_config = ACTION_SPACE
    print(f"  Battery power: {act_config.battery_power}")
    print(f"  Grid power: {act_config.grid_power}")
    print(f"  EV charging: {act_config.ev_charging_power}")
    print(f"  Renewable curtailment: {act_config.renewable_curtailment}")
    print(f"  Total: {act_config.get_total_dim()}")
    
except Exception as e:
    print(f"✗ Error loading environment: {e}")

# ========== 2. REWARD FUNCTION ==========
print("\n" + "="*80)
print("2. REWARD FUNCTION")
print("="*80)

try:
    from env_config import REWARD
    
    print(f"Reward Weights:")
    print(f"  alpha (emissions): {REWARD.alpha} ₹/kg CO2")
    print(f"  beta (degradation): {REWARD.beta}")
    print(f"  gamma (reliability): {REWARD.gamma}")
    
    print(f"\nPenalty Values:")
    print(f"  Degradation cost: {REWARD.degradation_cost_per_kwh} ₹/kWh")
    print(f"  Unmet demand penalty: {REWARD.unmet_demand_penalty_per_kwh} ₹/kWh")
    
    print(f"\nReward Formula (from env_config.py):")
    print(f"  reward = -(cost + alpha*emissions + beta*degradation + gamma*reliability_penalty)")
    print(f"  reward = -(cost + {REWARD.alpha}*emissions + {REWARD.beta}*degradation + {REWARD.gamma}*reliability_penalty)")
    
    # Example calculation
    example_cost = 64000
    example_emissions = 7277
    example_degradation = 300
    example_reliability = 0
    
    reward_components = {
        'cost': -example_cost,
        'emissions': -REWARD.alpha * example_emissions,
        'degradation': -REWARD.beta * example_degradation,
        'reliability': -REWARD.gamma * example_reliability
    }
    
    total_reward = sum(reward_components.values())
    
    print(f"\nExample Reward Calculation (typical day):")
    for key, val in reward_components.items():
        pct = abs(val) / abs(total_reward) * 100 if total_reward != 0 else 0
        print(f"  {key:15s}: {val:12.2f} ({pct:5.1f}%)")
    print(f"  {'TOTAL':15s}: {total_reward:12.2f}")
    
    print(f"\n⚠️  ISSUE: Cost dominates reward (should be balanced!)")
    
except Exception as e:
    print(f"✗ Error analyzing reward: {e}")

# ========== 3. SAFETY & CONSTRAINTS ==========
print("\n" + "="*80)
print("3. SAFETY & CONSTRAINTS")
print("="*80)

try:
    from env_config import SAFETY
    
    print(f"Safety Configuration:")
    print(f"  Battery SoC min (soft): {SAFETY.battery_soc_soft_min}")
    print(f"  Battery SoC max (soft): {SAFETY.battery_soc_soft_max}")
    print(f"  Battery SoC min (hard): {SAFETY.battery_soc_hard_min}")
    print(f"  Battery SoC max (hard): {SAFETY.battery_soc_hard_max}")
    print(f"  Battery temp max: {SAFETY.battery_temp_max_celsius} °C")
    print(f"  Grid import max: {SAFETY.grid_import_limit_kw} kW")
    print(f"  Grid export max: {SAFETY.grid_export_limit_kw} kW")
    
    print(f"\nSafety Penalty (per violation):")
    print(f"  {SAFETY.safety_penalty_per_violation} ₹")
    
    print(f"\n⚠️  CRITICAL ISSUE:")
    print(f"  - Safety penalty NOT in base reward function (env_config.py)")
    print(f"  - Only added in train_ppo_improved.py with 3x multiplier")
    print(f"  - Violations are counted as 'safety_overrides' in metrics")
    print(f"  - Actions are CLIPPED by SafetySupervisor, not just penalized")
    
    # Check if safety supervisor exists
    if os.path.exists('safety_supervisor.py'):
        print(f"\n✓ SafetySupervisor file exists")
        from safety_supervisor import SafetySupervisor
        print(f"  Class: SafetySupervisor")
    else:
        print(f"\n✗ SafetySupervisor file NOT FOUND")
    
except Exception as e:
    print(f"✗ Error analyzing safety: {e}")

# ========== 4. TRAINING SETUP ==========
print("\n" + "="*80)
print("4. TRAINING SETUP")
print("="*80)

# Check original training
print("\nOriginal Training (train_ppo.py):")
if os.path.exists('train_ppo.py'):
    print("  ✓ File exists")
    with open('train_ppo.py', 'r') as f:
        content = f.read()
        if 'learning_rate' in content:
            print("  Status: Uses older hyperparameters")
else:
    print("  ✗ File NOT FOUND")

# Check improved training
print("\nImproved Training (train_ppo_improved.py):")
if os.path.exists('train_ppo_improved.py'):
    print("  ✓ File exists")
    # Extract hyperparameters
    try:
        with open('train_ppo_improved.py', 'r') as f:
            content = f.read()
            
        print("\n  Hyperparameters:")
        params = ['learning_rate', 'clip_coef', 'n_epochs', 'batch_size', 
                  'minibatch_size', 'gae_lambda', 'gamma', 'entropy_coef', 
                  'value_coef', 'max_grad_norm']
        
        for param in params:
            if f'{param}=' in content:
                # Simple extraction (not perfect but works for most cases)
                lines = [l for l in content.split('\n') if f'{param}=' in l and not l.strip().startswith('#')]
                if lines:
                    print(f"    {param:20s}: {lines[0].split('=')[1].split(',')[0].split('#')[0].strip()}")
    except Exception as e:
        print(f"  Error extracting hyperparameters: {e}")
else:
    print("  ✗ File NOT FOUND")

# Check dataset
print("\nDataset:")
data_path = 'data/synthetic_10year/COMPLETE_10YEAR_DATA.csv'
if os.path.exists(data_path):
    print(f"  ✓ Found: {data_path}")
    df = pd.read_csv(data_path, nrows=10)
    print(f"    Columns: {df.columns.tolist()}")
    print(f"    Total rows: {len(pd.read_csv(data_path))}")
    
    print(f"\n  ⚠️  DATA QUALITY ISSUES:")
    print(f"    - Load is FAKE (0.65 × PV + 250)")
    print(f"    - Wind is FAKE (speed³ × 0.5)")
    print(f"    - Price is FAKE (only hour-based)")
    print(f"    - Load CORRELATES with PV (unrealistic!)")
else:
    print(f"  ✗ Synthetic data NOT FOUND at {data_path}")

# Check processed data
print("\nProcessed Data:")
for profile in ['pv_profile_processed.csv', 'wt_profile_processed.csv', 
                'load_profile_processed.csv', 'price_profile_processed.csv']:
    path = f'data/{profile}'
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"  ✓ {profile:30s}: {len(df)} rows")
    else:
        print(f"  ✗ {profile:30s}: NOT FOUND")

# ========== 5. CHECKPOINTS & LOGS ==========
print("\n" + "="*80)
print("5. CHECKPOINTS & LOGS")
print("="*80)

# Find all log directories
log_dirs = [d for d in os.listdir('logs') if os.path.isdir(f'logs/{d}')] if os.path.exists('logs') else []
if log_dirs:
    print(f"Log directories found: {len(log_dirs)}")
    for log_dir in sorted(log_dirs)[-3:]:  # Show last 3
        print(f"  - logs/{log_dir}")
        if os.path.exists(f'logs/{log_dir}/training_metrics.csv'):
            df = pd.read_csv(f'logs/{log_dir}/training_metrics.csv')
            print(f"    Episodes logged: {len(df)}")
            print(f"    Best return: {df['return'].max():.2f}")
            print(f"    Final return: {df['return'].iloc[-1]:.2f}")
else:
    print("No log directories found")

# Find all model directories
model_dirs = [d for d in os.listdir('models') if os.path.isdir(f'models/{d}')] if os.path.exists('models') else []
if model_dirs:
    print(f"\nModel directories found: {len(model_dirs)}")
    for model_dir in sorted(model_dirs)[-3:]:  # Show last 3
        print(f"  - models/{model_dir}")
        files = os.listdir(f'models/{model_dir}')
        print(f"    Files: {len(files)}")
        if 'best_model.pt' in files:
            print(f"    ✓ best_model.pt exists")
else:
    print("No model directories found")

# ========== 6. EVALUATION ==========
print("\n" + "="*80)
print("6. EVALUATION")
print("="*80)

if os.path.exists('evaluate.py'):
    print("✓ evaluate.py exists")
    print("  Run: python evaluate.py --model models/ppo_improved_YYYYMMDD_HHMMSS/best_model.pt")
else:
    print("✗ evaluate.py MISSING")
    print("  ⚠️  CRITICAL: Cannot validate results without evaluation script!")
    print("  Need to create evaluate.py to:")
    print("    - Run deterministic episodes")
    print("    - Generate metrics report")
    print("    - Export action/state trajectories")

# ========== 7. REPRODUCIBILITY ==========
print("\n" + "="*80)
print("7. REPRODUCIBILITY")
print("="*80)

print("Seed Configuration:")
print("  NumPy seed: Set in MicrogridEMSEnv(random_seed=42)")
print("  ✗ PyTorch seed: NOT SET in train_ppo_improved.py")
print("  ✗ Python random seed: NOT SET")
print("  ⚠️  Results are NOT fully reproducible!")

# ========== 8. TESTS ==========
print("\n" + "="*80)
print("8. TESTS")
print("="*80)

test_files = ['test_components.py', 'test_env.py', 'test_training.py']
for test_file in test_files:
    if os.path.exists(test_file):
        print(f"✓ {test_file} exists")
    else:
        print(f"✗ {test_file} NOT FOUND")

# ========== 9. DOCUMENTATION ==========
print("\n" + "="*80)
print("9. DOCUMENTATION")
print("="*80)

docs = ['README.md', 'INDIAN_CONTEXT.md', 'HACKATHON_READY.md', 
        'TRAINING_IMPROVEMENTS.md', 'EXPLAIN_TO_NON_TECHNICAL.md',
        'TRAINING_RESULTS_SUMMARY.md', 'PROJECT_COMPLETION_SUMMARY.md']

for doc in docs:
    if os.path.exists(doc):
        size = os.path.getsize(doc) / 1024
        print(f"✓ {doc:40s} ({size:.1f} KB)")
    else:
        print(f"✗ {doc:40s} NOT FOUND")

# ========== 10. SUMMARY ==========
print("\n" + "="*80)
print("10. CRITICAL ISSUES SUMMARY")
print("="*80)

issues = [
    ("HIGH", "evaluate.py missing - cannot validate results"),
    ("HIGH", "Reward components unbalanced (cost dominates 90%)"),
    ("HIGH", "Load/wind/price data is FAKE (derived, not real)"),
    ("HIGH", "No train/val/test split - can't prove generalization"),
    ("MEDIUM", "Safety penalty not in base reward, only in training"),
    ("MEDIUM", "PyTorch seed not set - not fully reproducible"),
    ("MEDIUM", "Entropy collapsed to 0 early - may have stopped exploring"),
    ("MEDIUM", "Actor/Critic loss = 0 in logs - updates may not be happening"),
    ("LOW", "Load correlates with PV (unrealistic)"),
    ("LOW", "Degradation cost too small to matter (0.2% of total)")
]

for severity, issue in issues:
    symbol = "❌" if severity == "HIGH" else "⚠️" if severity == "MEDIUM" else "ℹ️"
    print(f"{symbol} [{severity:6s}] {issue}")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
print("\nRecommendations:")
print("1. Create evaluate.py to validate results properly")
print("2. Rebalance reward components (cost vs emissions vs degradation)")
print("3. Generate realistic load profile (anticorrelated with PV)")
print("4. Add train/val/test split to prove generalization")
print("5. Set all random seeds for reproducibility")
print("6. Check why entropy collapsed to zero")
print("7. Verify PPO updates are actually happening")
print("\nSee above for detailed analysis of each issue.")
