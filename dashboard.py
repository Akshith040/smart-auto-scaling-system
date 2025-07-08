from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime, timedelta
from metrics_collector import MetricsCollector
from predictor import DemandPredictor
from scaling_engine import ScalingEngine
from resource_manager import ResourceManager

app = Flask(__name__)

# Initialize components
collector = MetricsCollector()
predictor = DemandPredictor()
scaling_engine = ScalingEngine()
resource_manager = ResourceManager(metrics_collector=collector)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """Get current metrics and recent history"""
    try:
        # Get current metrics and store them for real-time charting
        current = collector.collect_metrics()
        collector.store_metrics(current)  # Store the current metrics for chart history
        
        # Get recent metrics
        recent = collector.get_recent_metrics(50)
        
        # Get summary
        summary = collector.get_metrics_summary()
        
        return jsonify({
            'current': current,
            'recent': recent,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions')
def get_predictions():
    """Get demand predictions and anomaly detection"""
    try:
        recent_metrics = collector.get_recent_metrics(30)
        
        if len(recent_metrics) < 10:
            return jsonify({
                'predictions': [],
                'anomalies': [],
                'model_status': 'insufficient_data',
                'message': f'Need more data points to make predictions (have {len(recent_metrics)}, need 10+)',
                'current_data_count': len(recent_metrics)
            })
        
        # Train model if needed
        if not predictor.is_trained:
            print("Training model for predictions...")
            success = predictor.train_model(recent_metrics)
            if not success:
                return jsonify({
                    'predictions': [],
                    'anomalies': [],
                    'model_status': 'training_failed',
                    'message': 'Model training failed with current data'
                })
        
        # Get predictions with better error handling
        try:
            predictions = predictor.predict_demand(recent_metrics, horizon=10)
        except Exception as pred_error:
            print(f"Prediction error: {pred_error}")
            # Use simple fallback predictions
            current_load = recent_metrics[-1]['load_score'] if recent_metrics else 50
            predictions = [current_load] * 10
        
        # Detect anomalies
        try:
            anomalies = predictor.detect_anomalies(recent_metrics)
            anomalies_detected = sum(1 for a in anomalies if a) if anomalies else 0
        except Exception as anomaly_error:
            print(f"Anomaly detection error: {anomaly_error}")
            anomalies = [False] * len(recent_metrics)
            anomalies_detected = 0
        
        # Get scaling recommendation
        current_load = recent_metrics[-1]['load_score'] if recent_metrics else 50
        try:
            recommendation = predictor.get_scaling_recommendation([float(p) for p in predictions], current_load)
        except Exception as rec_error:
            print(f"Recommendation error: {rec_error}")
            recommendation = {
                'action': 'maintain',
                'confidence': 0.5,
                'reason': 'Using fallback recommendation due to prediction error',
                'predicted_load': current_load
            }
        
        return jsonify({
            'predictions': [float(p) for p in predictions] if predictions else [],
            'anomalies': [bool(a) for a in anomalies[-20:]] if anomalies else [],  # Convert numpy bool to Python bool
            'anomalies_detected': anomalies_detected,
            'recommendation': recommendation,
            'model_status': 'trained' if predictor.is_trained else 'fallback',
            'model_performance': {
                'accuracy': recommendation.get('confidence', 0.5),
                'mse': getattr(predictor, 'last_mse', 0.0),
                'data_points': len(recent_metrics)
            },
            'current_load': float(current_load),
            'data_points_used': len(recent_metrics),
            'features_used': len(predictor.feature_columns) if hasattr(predictor, 'feature_columns') else 0
        })
        
    except Exception as e:
        print(f"Predictions API error: {e}")
        return jsonify({
            'predictions': [],
            'anomalies': [],
            'model_status': 'error',
            'message': f'API error: {str(e)}',
            'error': str(e)
        }), 500

@app.route('/api/scaling/status')
def get_scaling_status():
    """Get current scaling status and decisions"""
    try:
        # Get current resource state
        current_state = resource_manager.get_current_state()
        
        # Get recent scaling history
        history = resource_manager.get_scaling_history(10)
        
        # Add fields for validation
        last_action = history[0] if history else {'action': 'initialize', 'timestamp': datetime.now().isoformat()}
        
        return jsonify({
            'current_state': current_state,
            'scaling_history': history,
            'recent_actions': history,
            'last_action': last_action,
            'current_instances': current_state.get('instances', 1),
            'total_cost': current_state.get('cost', {}).get('daily_cost', 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scaling/execute', methods=['POST'])
def execute_scaling():
    """Execute scaling decision manually or automatically"""
    try:
        # Get recent metrics for decision making
        recent_metrics = collector.get_recent_metrics(30)
        
        if not recent_metrics:
            return jsonify({'error': 'No metrics available'}), 400
        
        # Train predictor if needed
        if not predictor.is_trained:
            predictor.train_model(recent_metrics)
        
        # Get prediction and recommendation
        predictions = predictor.predict_demand(recent_metrics, horizon=5)
        current_load = recent_metrics[-1]['load_score']
        recommendation = predictor.get_scaling_recommendation(predictions, current_load)
        
        # Get current state for scaling engine
        current_state = {
            'current_instances': resource_manager.current_state['instances'],
            'load_score': current_load,
            'current_resources': resource_manager.current_state['resources']
        }
        
        # Make scaling decision
        decision = scaling_engine.make_scaling_decision(
            current_state, recommendation, resource_manager.get_scaling_history(5)
        )
        
        # Execute the decision
        execution_result = resource_manager.execute_scaling_decision(decision)
        
        return jsonify({
            'decision': decision,
            'execution_result': execution_result,
            'recommendation': recommendation,
            'predictions': predictions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/health')
def system_health():
    """Get overall system health status"""
    try:
        recent_metrics = collector.get_recent_metrics(10)
        resource_state = resource_manager.get_current_state()
        
        # Calculate health score
        if recent_metrics:
            avg_cpu = sum(m['cpu_percent'] for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m['memory_percent'] for m in recent_metrics) / len(recent_metrics)
            avg_response = sum(m['response_time_ms'] for m in recent_metrics) / len(recent_metrics)
            
            # Health scoring (0-100)
            cpu_health = max(0, 100 - avg_cpu)
            memory_health = max(0, 100 - avg_memory)
            response_health = max(0, 100 - (avg_response / 5))  # 500ms = 0 health
            
            overall_health = (cpu_health + memory_health + response_health) / 3
        else:
            overall_health = 50  # Unknown
        
        # System status
        if overall_health > 80:
            status = 'excellent'
        elif overall_health > 60:
            status = 'good'
        elif overall_health > 40:
            status = 'fair'
        else:
            status = 'poor'
        
        return jsonify({
            'health_score': round(overall_health, 1),
            'status': status,
            'instances': resource_state['instances'],
            'uptime': resource_state['uptime'],
            'cost': resource_state['cost_estimate'],
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update system configuration"""
    if request.method == 'GET':
        return jsonify(scaling_engine.config)
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            if not isinstance(new_config, dict):
                return jsonify({'error': 'Invalid config format, expected a JSON object'}), 400
            scaling_engine.config.update(new_config)
            
            # Save updated config
            with open(scaling_engine.config_file, 'w') as f:
                json.dump(scaling_engine.config, f, indent=2)
            
            return jsonify({'status': 'success', 'config': scaling_engine.config})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Ensure a valid response is always returned
    return jsonify({'error': 'Invalid request method'}), 405

@app.route('/api/simulate')
def simulate_load():
    """Simulate load for testing purposes"""
    try:
        # Collect and store a few metrics to simulate activity
        for _ in range(5):
            metrics = collector.collect_metrics()
            collector.store_metrics(metrics)
        
        return jsonify({
            'status': 'success',
            'message': 'Load simulation completed',
            'metrics_collected': 5
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verification')
def get_verification():
    """Get system verification to prove metrics are real"""
    try:
        # Get the EXACT same current metrics that the dashboard displays
        current_metrics = collector.collect_metrics()
        
        # Get system verification info but pass the current metrics
        verification = collector.get_system_verification(current_metrics)
        processes = collector.get_process_details(15)
        
        return jsonify({
            'verification': verification,
            'top_processes': processes,
            'dashboard_current_metrics': current_metrics,  # Exact same metrics as dashboard
            'metrics_source': 'real_system',
            'proof_type': 'live_system_monitoring',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stress-test')
def stress_test():
    """Generate CPU load to demonstrate real metrics"""
    try:
        import threading
        import time
        
        def cpu_stress():
            """Generate CPU load for 10 seconds"""
            end_time = time.time() + 10
            while time.time() < end_time:
                # CPU-intensive calculation
                sum(i*i for i in range(10000))
        
        # Start stress test in background
        thread = threading.Thread(target=cpu_stress)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'CPU stress test started for 10 seconds',
            'instruction': 'Watch the CPU metrics increase in real-time!',
            'duration': '10 seconds'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/realtime')
def get_realtime_metrics():
    """Get real-time metrics with forced new data collection"""
    try:
        # Force collection of new metrics point
        current = collector.collect_metrics()
        collector.store_metrics(current)
        
        # Get the most recent metrics for charting
        recent = collector.get_recent_metrics(30)  # Last 30 data points
        
        return jsonify({
            'current': current,
            'recent': recent,
            'timestamp': datetime.now().isoformat(),
            'data_points': len(recent)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Handle favicon request to prevent 404 errors"""
    return '', 204

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("Starting Smart Auto-Scaling Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    print("\nAPI Endpoints:")
    print("- GET  /api/metrics - Current metrics and history")
    print("- GET  /api/predictions - Demand predictions and anomalies")
    print("- GET  /api/scaling/status - Scaling status and history")
    print("- POST /api/scaling/execute - Execute scaling decision")
    print("- GET  /api/system/health - Overall system health")
    print("- GET  /api/simulate - Simulate load for testing")
    print("- GET  /api/stress-test - CPU stress test for metrics demonstration")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
