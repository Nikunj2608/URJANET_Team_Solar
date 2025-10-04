"""
Cloud Dashboard API for Real-Time Monitoring
Provides REST API endpoints and WebSocket support for real-time EMS monitoring
Integrates with anomaly detection and predictive maintenance system

Features:
- REST API for health indices, alerts, and recommendations
- WebSocket for real-time data streaming
- IoT data ingestion endpoints
- Alert notification system
- Maintenance scheduling
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict
import numpy as np

# Import microgrid environment and anomaly detection
# (In production, this would be running in a separate process)


class CloudEMSAPI:
    """Cloud-based EMS API for real-time monitoring and control"""
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for frontend access
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.host = host
        self.port = port
        
        # Data storage (in production, use Redis or similar)
        self.current_state = {}
        self.health_data = {}
        self.alerts = []
        self.recommendations = []
        self.historical_data = []
        
        # Monitoring flag
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Setup routes
        self._setup_routes()
        self._setup_websocket_handlers()
        
    def _setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/')
        def index():
            return jsonify({
                'service': 'Smart EMS Cloud API',
                'version': '1.0.0',
                'status': 'operational',
                'endpoints': {
                    'health': '/api/health',
                    'system_status': '/api/system/status',
                    'component_health': '/api/components/health',
                    'alerts': '/api/alerts',
                    'alerts_active': '/api/alerts/active',
                    'maintenance': '/api/maintenance/recommendations',
                    'diagnostics': '/api/diagnostics',
                    'real_time_data': '/api/realtime/data',
                    'iot_ingest': '/api/iot/ingest (POST)',
                }
            })
        
        @self.app.route('/api/health')
        def api_health():
            """API health check"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'monitoring_active': self.monitoring_active
            })
        
        @self.app.route('/api/system/status')
        def system_status():
            """Get overall system status"""
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'status': self.current_state.get('status', 'unknown'),
                'health_summary': self.health_data.get('summary', {}),
                'active_components': self.current_state.get('active_components', 0),
                'total_alerts': len(self.alerts),
                'critical_alerts': len([a for a in self.alerts if a.get('severity') == 'critical']),
                'pending_maintenance': len(self.recommendations)
            })
        
        @self.app.route('/api/components/health')
        def component_health():
            """Get health indices for all components"""
            component_id = request.args.get('component_id')
            
            if component_id:
                # Return specific component
                component_data = self.health_data.get('components', {}).get(component_id)
                if component_data:
                    return jsonify({
                        'component_id': component_id,
                        'data': component_data
                    })
                else:
                    return jsonify({'error': 'Component not found'}), 404
            else:
                # Return all components
                return jsonify({
                    'timestamp': datetime.now().isoformat(),
                    'components': self.health_data.get('components', {})
                })
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """Get all alerts (paginated)"""
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            severity = request.args.get('severity')
            
            alerts = self.alerts
            
            # Filter by severity if specified
            if severity:
                alerts = [a for a in alerts if a.get('severity') == severity]
            
            # Paginate
            total = len(alerts)
            alerts_page = alerts[offset:offset + limit]
            
            return jsonify({
                'total': total,
                'limit': limit,
                'offset': offset,
                'alerts': alerts_page
            })
        
        @self.app.route('/api/alerts/active')
        def get_active_alerts():
            """Get currently active alerts"""
            # Filter alerts from last 24 hours
            cutoff_time = datetime.now().timestamp() - 86400
            active_alerts = [
                a for a in self.alerts 
                if datetime.fromisoformat(a['timestamp']).timestamp() > cutoff_time
            ]
            
            return jsonify({
                'count': len(active_alerts),
                'alerts': active_alerts
            })
        
        @self.app.route('/api/maintenance/recommendations')
        def get_maintenance_recommendations():
            """Get predictive maintenance recommendations"""
            urgency = request.args.get('urgency')
            
            recommendations = self.recommendations
            
            if urgency:
                recommendations = [r for r in recommendations if r.get('urgency') == urgency]
            
            # Sort by priority
            recommendations = sorted(
                recommendations,
                key=lambda x: {'critical': 0, 'warning': 1, 'info': 2}.get(x.get('urgency', 'info'), 3)
            )
            
            return jsonify({
                'count': len(recommendations),
                'recommendations': recommendations
            })
        
        @self.app.route('/api/diagnostics')
        def get_diagnostics():
            """Get diagnostic insights"""
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'insights': self.health_data.get('diagnostic_insights', [])
            })
        
        @self.app.route('/api/realtime/data')
        def get_realtime_data():
            """Get real-time operational data"""
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'data': self.current_state.get('realtime', {})
            })
        
        @self.app.route('/api/iot/ingest', methods=['POST'])
        def ingest_iot_data():
            """Ingest IoT sensor data"""
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['component_id', 'timestamp', 'measurements']
                if not all(field in data for field in required_fields):
                    return jsonify({'error': 'Missing required fields'}), 400
                
                # Process the data (in production, add to queue for processing)
                self._process_iot_data(data)
                
                # Broadcast to WebSocket clients
                self.socketio.emit('iot_data', data)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Data ingested successfully',
                    'component_id': data['component_id']
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/schedule/maintenance', methods=['POST'])
        def schedule_maintenance():
            """Schedule maintenance activity"""
            try:
                data = request.get_json()
                
                required_fields = ['component_id', 'maintenance_type', 'scheduled_date']
                if not all(field in data for field in required_fields):
                    return jsonify({'error': 'Missing required fields'}), 400
                
                # Add to schedule (in production, store in database)
                maintenance_id = f"MAINT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                return jsonify({
                    'status': 'success',
                    'maintenance_id': maintenance_id,
                    'message': 'Maintenance scheduled successfully'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers for real-time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f'Client connected: {request.sid}')
            emit('connection_status', {
                'status': 'connected',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f'Client disconnected: {request.sid}')
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Subscribe to specific data streams"""
            stream_type = data.get('stream_type', 'all')
            print(f'Client {request.sid} subscribed to: {stream_type}')
            emit('subscription_confirmed', {
                'stream_type': stream_type,
                'timestamp': datetime.now().isoformat()
            })
    
    def _process_iot_data(self, data: Dict):
        """Process incoming IoT data"""
        # Store in historical data
        self.historical_data.append(data)
        
        # Keep only last 10000 records in memory
        if len(self.historical_data) > 10000:
            self.historical_data = self.historical_data[-10000:]
        
        # Update current state
        component_id = data['component_id']
        if 'realtime' not in self.current_state:
            self.current_state['realtime'] = {}
        
        self.current_state['realtime'][component_id] = data['measurements']
    
    def update_monitoring_data(self, monitoring_report: Dict):
        """Update monitoring data from environment"""
        # Update health data
        self.health_data = {
            'summary': monitoring_report.get('system_summary', {}),
            'components': monitoring_report.get('health_indices', {}),
            'diagnostic_insights': monitoring_report.get('diagnostic_insights', [])
        }
        
        # Update alerts
        new_alerts = monitoring_report.get('active_alerts', [])
        self.alerts.extend(new_alerts)
        
        # Keep last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        # Update recommendations
        self.recommendations = monitoring_report.get('maintenance_recommendations', [])
        
        # Broadcast updates via WebSocket
        self.socketio.emit('health_update', {
            'timestamp': datetime.now().isoformat(),
            'summary': monitoring_report.get('system_summary', {})
        })
        
        if new_alerts:
            self.socketio.emit('new_alerts', {
                'count': len(new_alerts),
                'alerts': new_alerts
            })
    
    def start_background_monitoring(self, env):
        """Start background thread for continuous monitoring"""
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Get monitoring report from environment
                    report = env.get_anomaly_report()
                    
                    # Update API data
                    self.update_monitoring_data(report)
                    
                    # Sleep for update interval
                    time.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    time.sleep(10)
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("Background monitoring started")
    
    def stop_background_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("Background monitoring stopped")
    
    def run(self, debug=False):
        """Run the Flask application"""
        print(f"Starting Cloud EMS API on {self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)


def create_sample_dashboard_html():
    """Create a sample HTML dashboard for visualization"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart EMS Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h2 {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #666; }
        .metric-value {
            font-weight: bold;
            font-size: 1.2em;
            color: #667eea;
        }
        .health-bar {
            width: 100%;
            height: 20px;
            background: #eee;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .health-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #ffc107, #dc3545);
            transition: width 0.3s;
        }
        .alert {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .alert.critical {
            background: #f8d7da;
            border-left-color: #dc3545;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-online { background: #28a745; }
        .status-warning { background: #ffc107; }
        .status-offline { background: #dc3545; }
        #connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div id="connection-status">
        <span class="status-indicator status-offline" id="status-dot"></span>
        <span id="status-text">Connecting...</span>
    </div>

    <div class="header">
        <h1>🔋 Smart Energy Management System</h1>
        <p>Real-Time Monitoring & Predictive Maintenance Dashboard</p>
    </div>

    <div class="dashboard">
        <div class="card">
            <h2>System Health</h2>
            <div class="metric">
                <span class="metric-label">Overall Health</span>
                <span class="metric-value" id="overall-health">--</span>
            </div>
            <div class="health-bar">
                <div class="health-fill" id="health-bar" style="width: 0%"></div>
            </div>
            <div class="metric">
                <span class="metric-label">Components Monitored</span>
                <span class="metric-value" id="components-count">--</span>
            </div>
            <div class="metric">
                <span class="metric-label">Critical Components</span>
                <span class="metric-value" id="critical-count">--</span>
            </div>
        </div>

        <div class="card">
            <h2>Active Alerts</h2>
            <div id="alerts-container">
                <p style="color: #999;">No active alerts</p>
            </div>
        </div>

        <div class="card">
            <h2>Maintenance Recommendations</h2>
            <div id="maintenance-container">
                <p style="color: #999;">No pending maintenance</p>
            </div>
        </div>

        <div class="card">
            <h2>Component Status</h2>
            <div id="components-container">
                <p style="color: #999;">Loading...</p>
            </div>
        </div>
    </div>

    <script>
        // Connect to WebSocket
        const socket = io('http://localhost:5000');
        
        socket.on('connect', () => {
            document.getElementById('status-dot').className = 'status-indicator status-online';
            document.getElementById('status-text').textContent = 'Connected';
            socket.emit('subscribe', { stream_type: 'all' });
            loadInitialData();
        });

        socket.on('disconnect', () => {
            document.getElementById('status-dot').className = 'status-indicator status-offline';
            document.getElementById('status-text').textContent = 'Disconnected';
        });

        socket.on('health_update', (data) => {
            updateHealthDisplay(data.summary);
        });

        socket.on('new_alerts', (data) => {
            updateAlertsDisplay(data.alerts);
        });

        function loadInitialData() {
            // Load system status
            fetch('http://localhost:5000/api/system/status')
                .then(r => r.json())
                .then(data => {
                    updateHealthDisplay(data.health_summary);
                });

            // Load alerts
            fetch('http://localhost:5000/api/alerts/active')
                .then(r => r.json())
                .then(data => {
                    updateAlertsDisplay(data.alerts);
                });

            // Load maintenance
            fetch('http://localhost:5000/api/maintenance/recommendations')
                .then(r => r.json())
                .then(data => {
                    updateMaintenanceDisplay(data.recommendations);
                });

            // Load components
            fetch('http://localhost:5000/api/components/health')
                .then(r => r.json())
                .then(data => {
                    updateComponentsDisplay(data.components);
                });
        }

        function updateHealthDisplay(summary) {
            if (!summary) return;
            document.getElementById('overall-health').textContent = 
                (summary.overall_health || 0).toFixed(1) + '%';
            document.getElementById('health-bar').style.width = 
                (summary.overall_health || 0) + '%';
            document.getElementById('components-count').textContent = 
                summary.components_monitored || 0;
            document.getElementById('critical-count').textContent = 
                summary.critical_components || 0;
        }

        function updateAlertsDisplay(alerts) {
            const container = document.getElementById('alerts-container');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<p style="color: #999;">No active alerts</p>';
                return;
            }
            
            container.innerHTML = alerts.slice(0, 5).map(alert => `
                <div class="alert ${alert.severity === 'critical' ? 'critical' : ''}">
                    <strong>${alert.type}</strong><br>
                    ${alert.description}<br>
                    <small>➜ ${alert.recommended_action}</small>
                </div>
            `).join('');
        }

        function updateMaintenanceDisplay(recommendations) {
            const container = document.getElementById('maintenance-container');
            if (!recommendations || recommendations.length === 0) {
                container.innerHTML = '<p style="color: #999;">No pending maintenance</p>';
                return;
            }
            
            container.innerHTML = recommendations.slice(0, 3).map(rec => `
                <div class="metric">
                    <div>
                        <div style="font-weight: bold;">${rec.component}</div>
                        <div style="font-size: 0.9em; color: #666;">${rec.description}</div>
                    </div>
                </div>
            `).join('');
        }

        function updateComponentsDisplay(components) {
            const container = document.getElementById('components-container');
            if (!components) return;
            
            container.innerHTML = Object.entries(components).map(([id, health]) => `
                <div class="metric">
                    <span class="metric-label">${id}</span>
                    <span class="metric-value">${health.overall_health?.toFixed(0) || '--'}%</span>
                </div>
            `).join('');
        }

        // Refresh data every 10 seconds
        setInterval(loadInitialData, 10000);
    </script>
</body>
</html>
    """
    
    with open('dashboard.html', 'w') as f:
        f.write(html_content)
    
    print("Sample dashboard created: dashboard.html")


if __name__ == "__main__":
    # Create sample dashboard
    create_sample_dashboard_html()
    
    # Create and run API
    api = CloudEMSAPI(host='0.0.0.0', port=5000)
    
    print("\n" + "=" * 80)
    print("🌐 Cloud EMS API Server")
    print("=" * 80)
    print(f"\nAPI Endpoints available at: http://localhost:5000")
    print(f"Dashboard: Open dashboard.html in your browser")
    print("\nAvailable endpoints:")
    print("  • GET  /api/system/status")
    print("  • GET  /api/components/health")
    print("  • GET  /api/alerts")
    print("  • GET  /api/alerts/active")
    print("  • GET  /api/maintenance/recommendations")
    print("  • GET  /api/diagnostics")
    print("  • POST /api/iot/ingest")
    print("\nWebSocket: ws://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("=" * 80 + "\n")
    
    try:
        api.run(debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
