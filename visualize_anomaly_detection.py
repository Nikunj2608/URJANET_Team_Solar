"""
Generate System Architecture Diagram for Anomaly Detection Module
Creates a visualization showing how the module integrates with the RL-based EMS
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Title
ax.text(8, 11.5, 'Smart EMS with Anomaly Detection & Predictive Maintenance', 
        ha='center', va='top', fontsize=20, fontweight='bold')
ax.text(8, 11.0, 'VidyutAI Hackathon 2025 - Problem Statement 2', 
        ha='center', va='top', fontsize=12, style='italic', color='gray')

# Color scheme
color_rl = '#667eea'
color_monitor = '#f6ad55'
color_iot = '#48bb78'
color_cloud = '#4299e1'
color_alert = '#fc8181'

def draw_box(ax, x, y, width, height, label, sublabel='', color='lightblue', textcolor='black'):
    """Draw a fancy box with label"""
    box = FancyBboxPatch((x, y), width, height,
                         boxstyle="round,pad=0.1", 
                         edgecolor='black', facecolor=color,
                         linewidth=2, alpha=0.8)
    ax.add_patch(box)
    ax.text(x + width/2, y + height/2 + 0.15, label,
           ha='center', va='center', fontsize=11, fontweight='bold', color=textcolor)
    if sublabel:
        ax.text(x + width/2, y + height/2 - 0.15, sublabel,
               ha='center', va='center', fontsize=8, color=textcolor, style='italic')

def draw_arrow(ax, x1, y1, x2, y2, label='', color='black', style='->'):
    """Draw an arrow with optional label"""
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle=style, color=color, linewidth=2,
                           mutation_scale=20, alpha=0.7)
    ax.add_patch(arrow)
    if label:
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x, mid_y + 0.1, label, ha='center', va='bottom',
               fontsize=8, color=color, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Layer 1: Physical Components (Bottom)
ax.text(8, 9.5, 'Physical Components (IoT Sensors)', ha='center', fontsize=12, fontweight='bold')
draw_box(ax, 0.5, 8.2, 2.2, 1.0, 'Battery Systems', 'SoC, SoH, Temp', color_iot, 'white')
draw_box(ax, 3.2, 8.2, 2.2, 1.0, 'Solar PV', 'Power, Irradiance', color_iot, 'white')
draw_box(ax, 5.9, 8.2, 2.2, 1.0, 'Wind Turbines', 'Power, Speed', color_iot, 'white')
draw_box(ax, 8.6, 8.2, 2.2, 1.0, 'EV Chargers', 'Power, Efficiency', color_iot, 'white')
draw_box(ax, 11.3, 8.2, 2.2, 1.0, 'Grid Connection', 'Voltage, Freq', color_iot, 'white')
draw_box(ax, 14.0, 8.2, 1.5, 1.0, 'Load', 'Demand', color_iot, 'white')

# Layer 2: Microgrid Environment
ax.text(8, 7.5, 'RL-Based Energy Management System', ha='center', fontsize=12, fontweight='bold')
draw_box(ax, 1.0, 6.0, 4.5, 1.2, 'Microgrid Environment', 'State, Actions, Rewards', color_rl, 'white')
draw_box(ax, 6.0, 6.0, 4.0, 1.2, 'Safety Supervisor', 'Constraint Enforcement', color_rl, 'white')
draw_box(ax, 10.5, 6.0, 4.0, 1.2, 'RL Agent (PPO)', 'Optimal Control', color_rl, 'white')

# Arrows from IoT to Environment
for i, x in enumerate([1.6, 4.3, 7.0, 9.7, 12.4, 14.75]):
    draw_arrow(ax, x, 8.2, x if i < 3 else x-1, 7.2, color=color_iot, style='->')

# Layer 3: NEW - Anomaly Detection System
ax.text(8, 5.2, '🔍 NEW: Anomaly Detection & Predictive Maintenance', 
        ha='center', fontsize=13, fontweight='bold', color=color_monitor)

# Component Health Monitors
draw_box(ax, 0.5, 3.5, 2.5, 1.4, 'Battery Monitor', 
         'Health, Degradation', color_monitor, 'black')
draw_box(ax, 3.5, 3.5, 2.5, 1.4, 'Solar PV Monitor', 
         'Performance Ratio', color_monitor, 'black')
draw_box(ax, 6.5, 3.5, 2.5, 1.4, 'EV Charger Monitor', 
         'Efficiency, Faults', color_monitor, 'black')

# Central Anomaly Detection System
draw_box(ax, 10.0, 3.2, 4.5, 2.0, 'Anomaly Detection\nSystem', 
         'Coordination & Analysis', color_monitor, 'black')

# Arrows from Environment to Monitors
draw_arrow(ax, 2.5, 6.0, 1.75, 4.9, 'State Updates', color=color_monitor)
draw_arrow(ax, 4.5, 6.0, 4.75, 4.9, '', color=color_monitor)
draw_arrow(ax, 7.0, 6.0, 7.75, 4.9, '', color=color_monitor)

# Arrows from Monitors to Central System
draw_arrow(ax, 3.0, 3.5, 10.0, 4.2, '', color=color_monitor)
draw_arrow(ax, 6.0, 3.5, 10.0, 4.0, '', color=color_monitor)
draw_arrow(ax, 9.0, 3.5, 10.0, 3.8, '', color=color_monitor)

# Layer 4: Outputs & Actions
ax.text(8, 2.5, 'Outputs & Cloud Integration', ha='center', fontsize=12, fontweight='bold')

# Health & Diagnostics
draw_box(ax, 0.5, 1.0, 2.8, 1.2, 'Health Indices', 
         'SoH, Performance', color_cloud, 'white')
draw_box(ax, 3.8, 1.0, 2.8, 1.2, 'Anomaly Alerts', 
         'Real-time Warnings', color_alert, 'white')
draw_box(ax, 7.1, 1.0, 2.8, 1.2, 'Maintenance Rec.', 
         'Cost Estimates', color_cloud, 'white')
draw_box(ax, 10.4, 1.0, 2.8, 1.2, 'Diagnostic Insights', 
         'Root Cause', color_cloud, 'white')
draw_box(ax, 13.7, 1.0, 1.8, 1.2, 'Reports', 
         'JSON', color_cloud, 'white')

# Arrows to outputs
for i, x in enumerate([1.9, 5.2, 8.5, 11.8, 14.6]):
    draw_arrow(ax, 12.25, 3.2, x, 2.2, color=color_cloud, style='->')

# Layer 5: Cloud Dashboard
draw_box(ax, 2.0, -0.5, 5.0, 0.8, '☁️ Cloud API Server', 
         'REST + WebSocket', '#e2e8f0', 'black')
draw_box(ax, 8.0, -0.5, 5.0, 0.8, '🌐 Web Dashboard', 
         'Real-time Visualization', '#e2e8f0', 'black')

# Arrows to cloud
draw_arrow(ax, 4.5, 1.0, 4.5, 0.3, color=color_cloud)
draw_arrow(ax, 10.5, 1.0, 10.5, 0.3, color=color_cloud)

# Add legend/key features box
legend_y = 0.2
features = [
    '✓ Real-time component health monitoring',
    '✓ Statistical anomaly detection',
    '✓ Predictive maintenance with cost estimates (₹)',
    '✓ Actionable alerts with remediation steps',
    '✓ Cloud-ready REST API + WebSocket',
    '✓ Seamless RL integration (zero code changes)'
]

# Side annotations
ax.text(15.5, 8.5, 'IoT Layer', rotation=90, ha='center', va='center', 
        fontsize=10, fontweight='bold', color=color_iot,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.text(15.5, 6.6, 'RL Layer', rotation=90, ha='center', va='center', 
        fontsize=10, fontweight='bold', color=color_rl,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.text(15.5, 4.2, 'Monitoring\nLayer', rotation=90, ha='center', va='center', 
        fontsize=10, fontweight='bold', color=color_monitor,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.text(15.5, 1.6, 'Output\nLayer', rotation=90, ha='center', va='center', 
        fontsize=10, fontweight='bold', color=color_cloud,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.text(15.5, -0.1, 'Cloud\nLayer', rotation=90, ha='center', va='center', 
        fontsize=10, fontweight='bold', color='gray',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig('anomaly_detection_architecture.png', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("✓ Architecture diagram saved: anomaly_detection_architecture.png")

# Create a second figure for the data flow
fig2, ax2 = plt.subplots(1, 1, figsize=(14, 10))
ax2.set_xlim(0, 14)
ax2.set_ylim(0, 10)
ax2.axis('off')

ax2.text(7, 9.5, 'Data Flow: Real-Time Monitoring & Anomaly Detection', 
         ha='center', va='top', fontsize=18, fontweight='bold')

# Step 1
draw_box(ax2, 1, 7.5, 3, 1.2, 'Step 1: State Update', 
         'env.step(action)', color_rl, 'white')
ax2.text(2.5, 6.8, '• Battery: SoC, SoH, Temp\n• PV: Power, Irradiance\n• Charger: Power, Efficiency',
         ha='center', fontsize=8)

# Step 2
draw_box(ax2, 5, 7.5, 3, 1.2, 'Step 2: Monitor Update', 
         'update_anomaly_detection()', color_monitor, 'black')
ax2.text(6.5, 6.8, '• Update component states\n• Calculate health indices\n• Store history',
         ha='center', fontsize=8)

# Step 3
draw_box(ax2, 9, 7.5, 4, 1.2, 'Step 3: Anomaly Detection', 
         'detect_all_anomalies()', color_monitor, 'black')
ax2.text(11, 6.8, '• Z-score analysis\n• Pattern matching\n• Severity classification',
         ha='center', fontsize=8)

# Arrows for steps 1-3
draw_arrow(ax2, 4, 8.1, 5, 8.1, 'state data', color_monitor)
draw_arrow(ax2, 8, 8.1, 9, 8.1, 'monitoring data', color_monitor)

# Step 4
draw_box(ax2, 1, 5.0, 3, 1.2, 'Step 4: Root Cause', 
         'generate_diagnostics()', color_cloud, 'white')
ax2.text(2.5, 4.3, '• Identify issue type\n• Determine root cause\n• Assess impact',
         ha='center', fontsize=8)

# Step 5
draw_box(ax2, 5, 5.0, 3, 1.2, 'Step 5: Recommendations', 
         'generate_maintenance()', color_cloud, 'white')
ax2.text(6.5, 4.3, '• Estimate RUL\n• Calculate costs\n• Prioritize actions',
         ha='center', fontsize=8)

# Step 6
draw_box(ax2, 9, 5.0, 4, 1.2, 'Step 6: Alert Generation', 
         'get_actionable_alerts()', color_alert, 'white')
ax2.text(11, 4.3, '• Format alerts\n• Add recommendations\n• Set severity',
         ha='center', fontsize=8)

# Arrows for steps 4-6
draw_arrow(ax2, 11, 7.5, 2.5, 6.2, '', color_cloud)
draw_arrow(ax2, 4, 5.6, 5, 5.6, 'diagnostics', color_cloud)
draw_arrow(ax2, 8, 5.6, 9, 5.6, 'recommendations', color_cloud)

# Step 7
draw_box(ax2, 3, 2.5, 3.5, 1.2, 'Step 7: Report', 
         'get_anomaly_report()', color_cloud, 'white')
ax2.text(4.75, 1.8, '• Comprehensive JSON\n• All insights\n• Ready for API',
         ha='center', fontsize=8)

# Step 8
draw_box(ax2, 7.5, 2.5, 3.5, 1.2, 'Step 8: Cloud API', 
         'REST + WebSocket', color_cloud, 'white')
ax2.text(9.25, 1.8, '• Serve via HTTP\n• Stream via WS\n• Store in DB',
         ha='center', fontsize=8)

# Arrows to final steps
draw_arrow(ax2, 11, 5.0, 4.75, 3.7, '', color_cloud)
draw_arrow(ax2, 6.5, 2.5, 7.5, 2.5, 'report', color_cloud)

# Step 9
draw_box(ax2, 4.5, 0.3, 5, 1.2, 'Step 9: Dashboard Display', 
         'Real-time Visualization', '#e2e8f0', 'black')

draw_arrow(ax2, 9.25, 2.5, 7, 1.5, '', color_cloud)

# Timing annotation
ax2.text(1, 0.2, 'Timing: Steps 1-6 run every 15 minutes (decision interval)\n' + 
         'Steps 7-9 available on-demand via API', 
         fontsize=9, style='italic', color='gray',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
plt.savefig('anomaly_detection_dataflow.png', dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print("✓ Data flow diagram saved: anomaly_detection_dataflow.png")

plt.show()

print("\n✅ Architecture diagrams generated successfully!")
print("   • anomaly_detection_architecture.png")
print("   • anomaly_detection_dataflow.png")
