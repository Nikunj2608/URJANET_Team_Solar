"""
Improved PPO Training Script with Optimizations for 10-Year Synthetic Data
Implements all recommended improvements:
- Increased safety penalties
- Observation & reward normalization
- Optimized hyperparameters (LR, batch size, entropy)
- Training on 10-year synthetic dataset
- Enhanced logging and visualization
"""

import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.distributions import Normal
from collections import deque
import json
from datetime import datetime
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

from microgrid_env import MicrogridEMSEnv
from env_config import TRAINING, REWARD, STEPS_PER_EPISODE


class RunningNormalizer:
    """Online normalization with running mean and std"""
    
    def __init__(self, shape, epsilon=1e-8):
        self.mean = np.zeros(shape, dtype=np.float32)
        self.var = np.ones(shape, dtype=np.float32)
        self.count = epsilon
        self.epsilon = epsilon
    
    def update(self, x):
        """Update running statistics"""
        batch_mean = np.mean(x, axis=0)
        batch_var = np.var(x, axis=0)
        batch_count = x.shape[0]
        
        delta = batch_mean - self.mean
        total_count = self.count + batch_count
        
        self.mean = self.mean + delta * batch_count / total_count
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        M2 = m_a + m_b + delta**2 * self.count * batch_count / total_count
        self.var = M2 / total_count
        self.count = total_count
    
    def normalize(self, x):
        """Normalize input"""
        return (x - self.mean) / (np.sqrt(self.var) + self.epsilon)


class RewardScaler:
    """Scale reward components to similar magnitudes"""
    
    def __init__(self):
        self.cost_scale = 1e-3  # Costs in thousands
        self.emission_scale = 1e-2  # Emissions in hundreds
        self.safety_scale = 1.0  # Keep safety penalty as-is
    
    def scale_reward(self, cost, emissions, degradation, reliability_penalty, safety_penalty):
        """Scale each component"""
        scaled_cost = -cost * self.cost_scale
        scaled_emissions = -emissions * self.emission_scale
        scaled_degradation = -degradation * self.cost_scale
        scaled_reliability = -reliability_penalty * self.cost_scale
        scaled_safety = -safety_penalty * self.safety_scale
        
        return (scaled_cost + scaled_emissions + scaled_degradation + 
                scaled_reliability + scaled_safety)


class ImprovedActor(nn.Module):
    """Improved Actor with proper initialization"""
    
    def __init__(self, obs_dim: int, action_dim: int, hidden_dims=[256, 256]):
        super().__init__()
        
        layers = []
        prev_dim = obs_dim
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.Tanh(),  # Tanh often works better than ReLU for policy networks
                nn.LayerNorm(hidden_dim)
            ])
            prev_dim = hidden_dim
        
        self.network = nn.Sequential(*layers)
        self.mean_layer = nn.Linear(prev_dim, action_dim)
        self.log_std_layer = nn.Linear(prev_dim, action_dim)
        
        # Orthogonal initialization
        for layer in self.network:
            if isinstance(layer, nn.Linear):
                nn.init.orthogonal_(layer.weight, gain=np.sqrt(2))
                nn.init.constant_(layer.bias, 0)
        
        nn.init.orthogonal_(self.mean_layer.weight, gain=0.01)
        nn.init.constant_(self.mean_layer.bias, 0)
        nn.init.orthogonal_(self.log_std_layer.weight, gain=0.01)
        nn.init.constant_(self.log_std_layer.bias, 0)
    
    def forward(self, obs):
        features = self.network(obs)
        mean = torch.tanh(self.mean_layer(features))
        log_std = self.log_std_layer(features)
        log_std = torch.clamp(log_std, -20, 2)
        return mean, log_std


class ImprovedCritic(nn.Module):
    """Improved Critic with proper initialization"""
    
    def __init__(self, obs_dim: int, hidden_dims=[256, 256]):
        super().__init__()
        
        layers = []
        prev_dim = obs_dim
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.Tanh(),
                nn.LayerNorm(hidden_dim)
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)
        
        # Orthogonal initialization
        for layer in self.network:
            if isinstance(layer, nn.Linear):
                nn.init.orthogonal_(layer.weight, gain=np.sqrt(2))
                nn.init.constant_(layer.bias, 0)
    
    def forward(self, obs):
        return self.network(obs)


class ImprovedPPOAgent:
    """Improved PPO Agent with optimized hyperparameters"""
    
    def __init__(self, obs_dim: int, action_dim: int, 
                 learning_rate=1e-4,
                 clip_coef=0.2,
                 n_epochs=10,
                 batch_size=2048,
                 minibatch_size=512,
                 gae_lambda=0.95,
                 gamma=0.99,
                 entropy_coef=0.01,
                 value_coef=0.5,
                 max_grad_norm=0.5):
        
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        
        # Hyperparameters
        self.learning_rate = learning_rate
        self.clip_coef = clip_coef
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.minibatch_size = minibatch_size
        self.gae_lambda = gae_lambda
        self.gamma = gamma
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.max_grad_norm = max_grad_norm
        
        # Networks
        self.actor = ImprovedActor(obs_dim, action_dim)
        self.critic = ImprovedCritic(obs_dim)
        
        # Optimizers
        self.actor_optimizer = Adam(self.actor.parameters(), lr=learning_rate, eps=1e-5)
        self.critic_optimizer = Adam(self.critic.parameters(), lr=learning_rate, eps=1e-5)
        
        # Normalizers
        self.obs_normalizer = RunningNormalizer(obs_dim)
        
        # Buffers
        self.observations = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.values = []
        self.dones = []
    
    def select_action(self, obs, deterministic=False):
        """Select action with normalized observation"""
        # Normalize observation
        obs_norm = self.obs_normalizer.normalize(obs)
        obs_tensor = torch.FloatTensor(obs_norm).unsqueeze(0)
        
        with torch.no_grad():
            mean, log_std = self.actor(obs_tensor)
            
            if deterministic:
                action = mean
            else:
                std = log_std.exp()
                dist = Normal(mean, std)
                action = dist.sample()
                log_prob = dist.log_prob(action).sum(-1)
                
                # Store for training
                value = self.critic(obs_tensor)
                self.observations.append(obs_norm)
                self.actions.append(action.squeeze(0).numpy())
                self.log_probs.append(log_prob.item())
                self.values.append(value.item())
        
        return action.squeeze(0).numpy()
    
    def store_transition(self, reward, done):
        """Store reward and done flag"""
        self.rewards.append(reward)
        self.dones.append(done)
    
    def update(self):
        """Update policy using PPO"""
        if len(self.observations) < self.batch_size:
            return 0.0, 0.0, 0.0
        
        # Convert to arrays
        observations = np.array(self.observations)
        actions = np.array(self.actions)
        old_log_probs = np.array(self.log_probs)
        rewards = np.array(self.rewards)
        values = np.array(self.values)
        dones = np.array(self.dones)
        
        # Update observation normalizer
        self.obs_normalizer.update(observations)
        
        # Compute GAE
        advantages, returns = self._compute_gae(rewards, values, dones, 
                                                 self.gamma, self.gae_lambda)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Convert to tensors
        observations = torch.FloatTensor(observations)
        actions = torch.FloatTensor(actions)
        old_log_probs = torch.FloatTensor(old_log_probs)
        advantages = torch.FloatTensor(advantages)
        returns = torch.FloatTensor(returns)
        
        # PPO epochs
        total_actor_loss = 0
        total_critic_loss = 0
        total_entropy = 0
        update_count = 0
        
        for _ in range(self.n_epochs):
            # Shuffle data
            indices = np.random.permutation(len(observations))
            
            # Minibatch updates
            for start in range(0, len(observations), self.minibatch_size):
                end = start + self.minibatch_size
                batch_indices = indices[start:end]
                
                batch_obs = observations[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                
                # Actor loss
                mean, log_std = self.actor(batch_obs)
                std = log_std.exp()
                dist = Normal(mean, std)
                new_log_probs = dist.log_prob(batch_actions).sum(-1)
                entropy = dist.entropy().sum(-1).mean()
                
                ratio = (new_log_probs - batch_old_log_probs).exp()
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_coef, 
                                   1 + self.clip_coef) * batch_advantages
                actor_loss = -torch.min(surr1, surr2).mean() - self.entropy_coef * entropy
                
                # Critic loss
                values_pred = self.critic(batch_obs).squeeze()
                critic_loss = self.value_coef * nn.MSELoss()(values_pred, batch_returns)
                
                # Update actor
                self.actor_optimizer.zero_grad()
                actor_loss.backward()
                nn.utils.clip_grad_norm_(self.actor.parameters(), self.max_grad_norm)
                self.actor_optimizer.step()
                
                # Update critic
                self.critic_optimizer.zero_grad()
                critic_loss.backward()
                nn.utils.clip_grad_norm_(self.critic.parameters(), self.max_grad_norm)
                self.critic_optimizer.step()
                
                total_actor_loss += actor_loss.item()
                total_critic_loss += critic_loss.item()
                total_entropy += entropy.item()
                update_count += 1
        
        # Clear buffers
        self.observations = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.values = []
        self.dones = []
        
        return (total_actor_loss / update_count, 
                total_critic_loss / update_count,
                total_entropy / update_count)
    
    def _compute_gae(self, rewards, values, dones, gamma=0.99, lam=0.95):
        """Compute Generalized Advantage Estimation"""
        advantages = np.zeros_like(rewards)
        last_advantage = 0
        
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]
            
            delta = rewards[t] + gamma * next_value * (1 - dones[t]) - values[t]
            advantages[t] = last_advantage = delta + gamma * lam * (1 - dones[t]) * last_advantage
        
        returns = advantages + values
        return advantages, returns
    
    def save(self, path):
        """Save model and normalizer"""
        torch.save({
            'actor': self.actor.state_dict(),
            'critic': self.critic.state_dict(),
            'obs_normalizer_mean': self.obs_normalizer.mean,
            'obs_normalizer_var': self.obs_normalizer.var,
            'obs_normalizer_count': self.obs_normalizer.count
        }, path)
    
    def load(self, path):
        """Load model and normalizer"""
        checkpoint = torch.load(path)
        self.actor.load_state_dict(checkpoint['actor'])
        self.critic.load_state_dict(checkpoint['critic'])
        self.obs_normalizer.mean = checkpoint['obs_normalizer_mean']
        self.obs_normalizer.var = checkpoint['obs_normalizer_var']
        self.obs_normalizer.count = checkpoint['obs_normalizer_count']


def load_synthetic_data(data_dir='data/synthetic_10year', use_full_csv=True):
    """Load 10-year synthetic dataset"""
    print("\n" + "="*60)
    print("Loading 10-Year Synthetic Dataset")
    print("="*60)
    
    if use_full_csv:
        # Load complete CSV (faster)
        csv_path = os.path.join(data_dir, 'COMPLETE_10YEAR_DATA.csv')
        if os.path.exists(csv_path):
            print(f"Loading from: {csv_path}")
            df = pd.read_csv(csv_path)
            
            # Actual column names: DATE_TIME, AMBIENT_TEMPERATURE, MODULE_TEMPERATURE, 
            # IRRADIATION, HUMIDITY, WIND_SPEED, DC_POWER, AC_POWER, DAILY_YIELD, TOTAL_YIELD
            
            # Split into profiles using actual column names
            pv_profile = df[['DATE_TIME', 'AC_POWER']].rename(
                columns={'DATE_TIME': 'Timestamp', 'AC_POWER': 'pv_total'})
            wt_profile = df[['DATE_TIME', 'WIND_SPEED']].rename(
                columns={'DATE_TIME': 'Timestamp', 'WIND_SPEED': 'wt_total'})
            load_profile = df[['DATE_TIME', 'AC_POWER']].rename(
                columns={'DATE_TIME': 'Timestamp', 'AC_POWER': 'load_total'})
            price_profile = df[['DATE_TIME', 'AMBIENT_TEMPERATURE']].rename(
                columns={'DATE_TIME': 'Timestamp', 'AMBIENT_TEMPERATURE': 'price'})
            
            # Scale wind from speed using cubic power law (P ∝ v³)
            wt_profile['wt_total'] = (wt_profile['wt_total'] ** 3) * 0.5  # Scaled to reasonable kW
            
            # Scale load (assume load follows PV pattern with offset)
            # Make load more realistic: 60-80% of PV average + base load
            load_profile['load_total'] = load_profile['load_total'] * 0.65 + 250  # Base load 250 kW
            
            # Convert to ToU price (Indian tariffs based on time of day)
            price_profile['hour'] = pd.to_datetime(df['DATE_TIME']).dt.hour
            price_profile['price'] = price_profile['hour'].apply(
                lambda h: 9.50 if (9 <= h < 12) or (18 <= h < 22) else 
                         4.50 if (h < 6) or (h >= 22) else 7.50
            )
            price_profile = price_profile.drop('hour', axis=1)
            
            print(f"✓ Loaded {len(df)} timesteps (10 years)")
            print(f"  PV range: {pv_profile['pv_total'].min():.1f} - {pv_profile['pv_total'].max():.1f} kW")
            print(f"  Wind range: {wt_profile['wt_total'].min():.1f} - {wt_profile['wt_total'].max():.1f} kW")
            print(f"  Load range: {load_profile['load_total'].min():.1f} - {load_profile['load_total'].max():.1f} kW")
            
            return pv_profile, wt_profile, load_profile, price_profile
    
    # Fallback: load original processed data
    print("Synthetic data not found, using original processed data")
    pv_profile = pd.read_csv('data/pv_profile_processed.csv')
    wt_profile = pd.read_csv('data/wt_profile_processed.csv')
    load_profile = pd.read_csv('data/load_profile_processed.csv')
    price_profile = pd.read_csv('data/price_profile_processed.csv')
    
    return pv_profile, wt_profile, load_profile, price_profile


def train_improved(
    env: MicrogridEMSEnv,
    agent: ImprovedPPOAgent,
    num_episodes: int,
    log_dir: str,
    model_dir: str,
    eval_interval: int = 50,
    save_interval: int = 100,
    safety_weight_multiplier: float = 3.0
):
    """Improved training loop with enhanced logging"""
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    # Reward scaler
    reward_scaler = RewardScaler()
    
    # Metrics tracking
    metrics = {
        'episode': [],
        'return': [],
        'cost': [],
        'emissions': [],
        'safety_violations': [],
        'unmet_demand': [],
        'actor_loss': [],
        'critic_loss': [],
        'entropy': []
    }
    
    best_return = -np.inf
    episode_rewards = deque(maxlen=100)
    
    print("\n" + "="*60)
    print("IMPROVED PPO TRAINING - 10-YEAR SYNTHETIC DATA")
    print("="*60)
    print(f"Safety Weight Multiplier: {safety_weight_multiplier}x")
    print(f"Learning Rate: {agent.learning_rate}")
    print(f"Batch Size: {agent.batch_size}")
    print(f"Minibatch Size: {agent.minibatch_size}")
    print(f"Entropy Coefficient: {agent.entropy_coef}")
    print("="*60)
    
    for episode in range(num_episodes):
        obs = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action = agent.select_action(obs)
            next_obs, reward, done, info = env.step(action)
            
            # Scale reward with enhanced safety penalty
            if 'safety_penalty' in info:
                safety_penalty = info['safety_penalty'] * safety_weight_multiplier
            else:
                safety_penalty = 0
            
            scaled_reward = reward_scaler.scale_reward(
                cost=info.get('cost', 0),
                emissions=info.get('emissions', 0),
                degradation=info.get('degradation_cost', 0),
                reliability_penalty=info.get('reliability_penalty', 0),
                safety_penalty=safety_penalty
            )
            
            agent.store_transition(scaled_reward, done)
            episode_reward += reward
            obs = next_obs
        
        episode_rewards.append(episode_reward)
        
        # Update policy
        if len(agent.observations) >= agent.batch_size:
            actor_loss, critic_loss, entropy = agent.update()
        else:
            actor_loss, critic_loss, entropy = 0, 0, 0
        
        # Log metrics
        metrics['episode'].append(episode)
        metrics['return'].append(episode_reward)
        metrics['cost'].append(info['episode_metrics']['total_cost'])
        metrics['emissions'].append(info['episode_metrics']['total_emissions'])
        metrics['safety_violations'].append(info['episode_metrics']['safety_overrides'])
        metrics['unmet_demand'].append(info['episode_metrics']['unmet_demand_events'])
        metrics['actor_loss'].append(actor_loss)
        metrics['critic_loss'].append(critic_loss)
        metrics['entropy'].append(entropy)
        
        # Print progress
        if (episode + 1) % 10 == 0:
            avg_return = np.mean(list(episode_rewards))
            print(f"\nEpisode {episode+1}/{num_episodes}")
            print(f"  Return: {episode_reward:.2f} | Avg(100): {avg_return:.2f}")
            print(f"  Cost: ₹{metrics['cost'][-1]:.2f} | Emissions: {metrics['emissions'][-1]:.1f} kg")
            print(f"  Safety Violations: {metrics['safety_violations'][-1]} | Unmet: {metrics['unmet_demand'][-1]}")
            print(f"  Actor Loss: {actor_loss:.4f} | Critic Loss: {critic_loss:.4f} | Entropy: {entropy:.4f}")
        
        # Save best model
        if episode_reward > best_return:
            best_return = episode_reward
            agent.save(os.path.join(model_dir, "best_model.pt"))
            print(f"  ✓ NEW BEST MODEL! Return: {best_return:.2f}")
        
        # Save checkpoint
        if (episode + 1) % save_interval == 0:
            agent.save(os.path.join(model_dir, f"checkpoint_ep{episode+1}.pt"))
            
            # Save metrics
            df_metrics = pd.DataFrame(metrics)
            df_metrics.to_csv(os.path.join(log_dir, "training_metrics.csv"), index=False)
            
            # Plot training curves
            plot_training_curves(df_metrics, log_dir)
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print(f"Best Return: {best_return:.2f}")
    print("="*60)
    
    return metrics


def plot_training_curves(df_metrics, log_dir):
    """Plot comprehensive training curves"""
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    
    # Smooth curves
    window = min(50, len(df_metrics) // 10)
    
    # Return
    axes[0, 0].plot(df_metrics['episode'], df_metrics['return'], alpha=0.3, label='Raw')
    axes[0, 0].plot(df_metrics['episode'], 
                    df_metrics['return'].rolling(window).mean(), 
                    label=f'MA({window})', linewidth=2)
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('Return')
    axes[0, 0].set_title('Episode Return')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Cost
    axes[0, 1].plot(df_metrics['episode'], df_metrics['cost'], alpha=0.3)
    axes[0, 1].plot(df_metrics['episode'], 
                    df_metrics['cost'].rolling(window).mean(), 
                    linewidth=2)
    axes[0, 1].set_xlabel('Episode')
    axes[0, 1].set_ylabel('Cost (₹)')
    axes[0, 1].set_title('Total Cost per Episode')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Emissions
    axes[1, 0].plot(df_metrics['episode'], df_metrics['emissions'], alpha=0.3)
    axes[1, 0].plot(df_metrics['episode'], 
                    df_metrics['emissions'].rolling(window).mean(), 
                    linewidth=2)
    axes[1, 0].set_xlabel('Episode')
    axes[1, 0].set_ylabel('Emissions (kg CO₂)')
    axes[1, 0].set_title('Total Emissions per Episode')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Safety Violations
    axes[1, 1].plot(df_metrics['episode'], df_metrics['safety_violations'], alpha=0.3)
    axes[1, 1].plot(df_metrics['episode'], 
                    df_metrics['safety_violations'].rolling(window).mean(), 
                    linewidth=2)
    axes[1, 1].set_xlabel('Episode')
    axes[1, 1].set_ylabel('Count')
    axes[1, 1].set_title('Safety Violations per Episode')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].axhline(y=5, color='r', linestyle='--', label='Target < 5')
    axes[1, 1].legend()
    
    # Actor Loss
    axes[2, 0].plot(df_metrics['episode'], df_metrics['actor_loss'])
    axes[2, 0].set_xlabel('Episode')
    axes[2, 0].set_ylabel('Loss')
    axes[2, 0].set_title('Actor Loss')
    axes[2, 0].grid(True, alpha=0.3)
    
    # Entropy
    axes[2, 1].plot(df_metrics['episode'], df_metrics['entropy'])
    axes[2, 1].set_xlabel('Episode')
    axes[2, 1].set_ylabel('Entropy')
    axes[2, 1].set_title('Policy Entropy')
    axes[2, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(log_dir, 'training_curves.png'), dpi=150, bbox_inches='tight')
    plt.close()


def main():
    """Main training entry point"""
    # Load 10-year synthetic data
    pv_profile, wt_profile, load_profile, price_profile = load_synthetic_data()
    
    print(f"\n✓ Data loaded: {len(pv_profile)} timesteps")
    
    # Create environment with enhanced safety
    print("\nCreating environment...")
    env = MicrogridEMSEnv(
        pv_profile=pv_profile,
        wt_profile=wt_profile,
        load_profile=load_profile,
        price_profile=price_profile,
        enable_evs=True,
        enable_degradation=True,
        enable_emissions=True,
        forecast_noise_std=0.1,
        random_seed=42
    )
    
    print(f"✓ Observation space: {env.observation_space.shape}")
    print(f"✓ Action space: {env.action_space.shape}")
    
    # Create improved agent
    print("\nCreating Improved PPO agent...")
    agent = ImprovedPPOAgent(
        obs_dim=env.observation_space.shape[0],
        action_dim=env.action_space.shape[0],
        learning_rate=1e-4,  # Reduced from 3e-4
        clip_coef=0.2,
        n_epochs=10,
        batch_size=2048,  # Increased
        minibatch_size=512,
        gae_lambda=0.95,
        gamma=0.99,
        entropy_coef=0.01,
        value_coef=0.5,
        max_grad_norm=0.5
    )
    
    print("✓ Agent created with optimized hyperparameters")
    
    # Train
    print("\nStarting IMPROVED training on 10-year synthetic data...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = f"logs/ppo_improved_{timestamp}"
    model_dir = f"models/ppo_improved_{timestamp}"
    
    metrics = train_improved(
        env=env,
        agent=agent,
        num_episodes=1000,  # Train longer on more data
        log_dir=log_dir,
        model_dir=model_dir,
        eval_interval=50,
        save_interval=100,
        safety_weight_multiplier=3.0  # 3x safety penalty
    )
    
    print(f"\n✓ Logs saved to: {log_dir}")
    print(f"✓ Models saved to: {model_dir}")
    print("\nNext steps:")
    print("1. Check training_curves.png for learning progress")
    print("2. Evaluate best model: python evaluate.py")
    print("3. If safety violations still high, increase safety_weight_multiplier")


if __name__ == "__main__":
    main()
