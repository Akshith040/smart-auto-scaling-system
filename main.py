import time
import threading
from datetime import datetime
from metrics_collector import MetricsCollector
from predictor import DemandPredictor
from scaling_engine import ScalingEngine
from resource_manager import ResourceManager

class AutoScalingOrchestrator:
    """Main orchestrator that coordinates all auto-scaling components"""
    
    def __init__(self):
        # Initialize all components
        self.metrics_collector = MetricsCollector()
        self.predictor = DemandPredictor()
        self.scaling_engine = ScalingEngine()
        self.resource_manager = ResourceManager()
        
        # Control variables
        self.running = False
        self.collection_interval = 60  # Collect metrics every 60 seconds
        self.scaling_interval = 300   # Check scaling every 5 minutes
        
        print("🚀 Smart Auto-Scaling System Initialized")
        print("=" * 50)
    
    def start_monitoring(self):
        """Start the monitoring and auto-scaling process"""
        self.running = True
        
        # Start metrics collection thread
        metrics_thread = threading.Thread(target=self._metrics_collection_loop, daemon=True)
        metrics_thread.start()
        
        # Start scaling decision thread
        scaling_thread = threading.Thread(target=self._scaling_decision_loop, daemon=True)
        scaling_thread.start()
        
        print("✅ Monitoring started")
        print("📊 Metrics collection interval: {} seconds".format(self.collection_interval))
        print("⚖️ Scaling check interval: {} seconds".format(self.scaling_interval))
        print("\nPress Ctrl+C to stop...\n")
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False
        print("\n🛑 Stopping auto-scaling system...")
        print("✅ System stopped gracefully")
    
    def _metrics_collection_loop(self):
        """Background thread for collecting metrics"""
        while self.running:
            try:
                # Collect current metrics
                metrics = self.metrics_collector.collect_metrics()
                self.metrics_collector.store_metrics(metrics)
                
                print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] "
                      f"CPU: {metrics['cpu_percent']:.1f}%, "
                      f"Memory: {metrics['memory_percent']:.1f}%, "
                      f"Load: {metrics['load_score']:.1f}")
                
            except Exception as e:
                print(f"❌ Metrics collection error: {e}")
            
            time.sleep(self.collection_interval)
    
    def _scaling_decision_loop(self):
        """Background thread for making scaling decisions"""
        while self.running:
            try:
                # Wait for initial metrics collection
                time.sleep(self.scaling_interval)
                
                if not self.running:
                    break
                
                # Get recent metrics
                recent_metrics = self.metrics_collector.get_recent_metrics(30)
                
                if len(recent_metrics) < 5:
                    print("⏳ Waiting for more metrics before making scaling decisions...")
                    continue
                
                # Train predictor if needed
                if not self.predictor.is_trained:
                    print("🤖 Training prediction model...")
                    success = self.predictor.train_model(recent_metrics)
                    if success:
                        print("✅ Model trained successfully")
                    else:
                        print("❌ Model training failed, using fallback predictions")
                
                # Get predictions and recommendation
                predictions = self.predictor.predict_demand(recent_metrics, horizon=5)
                current_load = recent_metrics[-1]['load_score']
                recommendation = self.predictor.get_scaling_recommendation(predictions, current_load)
                
                # Get current resource state
                current_state = {
                    'current_instances': self.resource_manager.current_state['instances'],
                    'load_score': current_load,
                    'current_resources': self.resource_manager.current_state['resources']
                }
                
                # Make scaling decision
                recent_decisions = self.resource_manager.get_scaling_history(5)
                decision = self.scaling_engine.make_scaling_decision(
                    current_state, recommendation, recent_decisions
                )
                
                # Log the decision
                print(f"\n🎯 [{datetime.now().strftime('%H:%M:%S')}] Scaling Decision:")
                print(f"   Action: {decision['action'].upper()}")
                print(f"   Confidence: {decision['confidence']:.1%}")
                print(f"   Reason: {decision['reason']}")
                
                if decision['action'] != 'maintain':
                    print(f"   Instances: {decision['current_instances']} → {decision['recommended_instances']}")
                    print(f"   Cost Impact: ${decision['cost_impact']['hourly_cost_change']:.2f}/hour")
                
                # Execute scaling decision
                if decision['action'] != 'maintain':
                    print("⚙️ Executing scaling action...")
                    execution_result = self.resource_manager.execute_scaling_decision(decision)
                    
                    if execution_result['status'] == 'completed':
                        print(f"✅ Scaling completed successfully in {execution_result['execution_time_seconds']:.1f}s")
                    else:
                        print(f"❌ Scaling failed: {execution_result.get('errors', ['Unknown error'])}")
                else:
                    print("➡️ No scaling action needed")
                
                print()  # Empty line for readability
                
            except Exception as e:
                print(f"❌ Scaling decision error: {e}")
            
            time.sleep(self.scaling_interval)
    
    def run_demo(self):
        """Run a quick demo of the system"""
        print("🎬 Running Auto-Scaling Demo")
        print("=" * 30)
        
        # Collect some initial metrics
        print("📊 Collecting initial metrics...")
        for i in range(5):
            metrics = self.metrics_collector.collect_metrics()
            self.metrics_collector.store_metrics(metrics)
            print(f"   Sample {i+1}: Load Score = {metrics['load_score']:.1f}")
            time.sleep(1)
        
        # Train the model
        print("\n🤖 Training prediction model...")
        recent_metrics = self.metrics_collector.get_recent_metrics()
        success = self.predictor.train_model(recent_metrics)
        
        if success:
            print("✅ Model trained successfully")
            
            # Make predictions
            print("\n🔮 Making predictions...")
            predictions = self.predictor.predict_demand(recent_metrics, horizon=5)
            print(f"   Next 5 predictions: {[f'{p:.1f}' for p in predictions]}")
            
            # Get recommendation
            current_load = recent_metrics[-1]['load_score']
            recommendation = self.predictor.get_scaling_recommendation(predictions, current_load)
            print(f"   Recommendation: {recommendation['action'].upper()} (confidence: {recommendation['confidence']:.1%})")
            print(f"   Reason: {recommendation['reason']}")
            
            # Make scaling decision
            print("\n⚖️ Making scaling decision...")
            current_state = {
                'current_instances': self.resource_manager.current_state['instances'],
                'load_score': current_load,
                'current_resources': self.resource_manager.current_state['resources']
            }
            
            decision = self.scaling_engine.make_scaling_decision(current_state, recommendation)
            print(f"   Decision: {decision['action'].upper()}")
            print(f"   Reason: {decision['reason']}")
            
            # Execute decision (simulation)
            if decision['action'] != 'maintain':
                print("\n⚙️ Executing scaling decision...")
                execution_result = self.resource_manager.execute_scaling_decision(decision)
                print(f"   Status: {execution_result['status'].upper()}")
                print(f"   Execution time: {execution_result['execution_time_seconds']:.1f}s")
            
        else:
            print("❌ Model training failed")
        
        print("\n✅ Demo completed!")
        print("\n💡 To start the full monitoring system, run:")
        print("   python main.py --monitor")
        print("\n🌐 To start the web dashboard, run:")
        print("   python dashboard.py")

def main():
    import sys
    
    orchestrator = AutoScalingOrchestrator()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--monitor':
        # Start full monitoring
        orchestrator.start_monitoring()
    else:
        # Run demo
        orchestrator.run_demo()

if __name__ == "__main__":
    main()
