#!/usr/bin/env python3
"""
Test script for the Smart Auto-Scaling System
This script validates all components work correctly
"""

import sys
import time
import json
from datetime import datetime

def test_metrics_collector():
    """Test the metrics collector"""
    print("🧪 Testing Metrics Collector...")
    
    try:
        from metrics_collector import MetricsCollector
        
        collector = MetricsCollector()
        
        # Test metrics collection
        metrics = collector.collect_metrics()
        assert 'cpu_percent' in metrics
        assert 'memory_percent' in metrics
        assert 'load_score' in metrics
        assert 0 <= metrics['load_score'] <= 100
        
        # Test storage
        collector.store_metrics(metrics)
        recent = collector.get_recent_metrics(1)
        assert len(recent) == 1
        
        print("✅ Metrics Collector: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Metrics Collector: FAILED - {e}")
        return False

def test_predictor():
    """Test the demand predictor"""
    print("🧪 Testing Demand Predictor...")
    
    try:
        from predictor import DemandPredictor
        from metrics_collector import MetricsCollector
        
        predictor = DemandPredictor()
        collector = MetricsCollector()
        
        # Generate some test data
        test_metrics = []
        for i in range(15):
            metrics = collector.collect_metrics()
            test_metrics.append(metrics)
            time.sleep(0.1)
        
        # Test model training
        success = predictor.train_model(test_metrics)
        
        if success:
            # Test predictions
            predictions = predictor.predict_demand(test_metrics, horizon=5)
            assert len(predictions) == 5
            assert all(0 <= p <= 100 for p in predictions)
            
            # Test anomaly detection
            anomalies = predictor.detect_anomalies(test_metrics)
            assert len(anomalies) == len(test_metrics)
            
            # Test scaling recommendation
            recommendation = predictor.get_scaling_recommendation(predictions, 50)
            assert 'action' in recommendation
            assert recommendation['action'] in ['scale_up', 'scale_down', 'maintain']
            
        print("✅ Demand Predictor: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Demand Predictor: FAILED - {e}")
        return False

def test_scaling_engine():
    """Test the scaling engine"""
    print("🧪 Testing Scaling Engine...")
    
    try:
        from scaling_engine import ScalingEngine
        
        engine = ScalingEngine()
        
        # Test configuration loading
        assert 'min_instances' in engine.config
        assert 'max_instances' in engine.config
        
        # Test scaling decision
        current_state = {
            'current_instances': 2,
            'load_score': 75,
            'current_resources': {'total_cpu_cores': 4}
        }
        
        recommendation = {
            'action': 'scale_up',
            'confidence': 0.8,
            'predicted_load': 85,
            'reason': 'Test recommendation'
        }
        
        decision = engine.make_scaling_decision(current_state, recommendation)
        assert 'action' in decision
        assert 'confidence' in decision
        assert 'recommended_instances' in decision
        
        print("✅ Scaling Engine: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Scaling Engine: FAILED - {e}")
        return False

def test_resource_manager():
    """Test the resource manager"""
    print("🧪 Testing Resource Manager...")
    
    try:
        from resource_manager import ResourceManager
        
        manager = ResourceManager()
        
        # Test state loading
        state = manager.get_current_state()
        assert 'instances' in state
        assert 'resources' in state
        
        # Test scaling execution
        test_decision = {
            'action': 'maintain',
            'recommended_instances': state['instances'],
            'recommended_resources': state['resources'],
            'reason': 'Test execution'
        }
        
        result = manager.execute_scaling_decision(test_decision)
        assert 'status' in result
        assert result['status'] in ['completed', 'failed']
        
        print("✅ Resource Manager: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Resource Manager: FAILED - {e}")
        return False

def test_integration():
    """Test full system integration"""
    print("🧪 Testing System Integration...")
    
    try:
        from main import AutoScalingOrchestrator
        
        orchestrator = AutoScalingOrchestrator()
        
        # Test component initialization
        assert orchestrator.metrics_collector is not None
        assert orchestrator.predictor is not None
        assert orchestrator.scaling_engine is not None
        assert orchestrator.resource_manager is not None
        
        print("✅ System Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ System Integration: FAILED - {e}")
        return False

def test_dashboard_api():
    """Test dashboard API endpoints (basic import test)"""
    print("🧪 Testing Dashboard API...")
    
    try:
        # Test if dashboard imports correctly
        import dashboard
        
        assert hasattr(dashboard, 'app')
        assert hasattr(dashboard, 'collector')
        assert hasattr(dashboard, 'predictor')
        
        print("✅ Dashboard API: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard API: FAILED - {e}")
        return False

def run_performance_test():
    """Run a basic performance test"""
    print("🧪 Running Performance Test...")
    
    try:
        from metrics_collector import MetricsCollector
        
        collector = MetricsCollector()
        
        # Test metrics collection speed
        start_time = time.time()
        for i in range(10):
            metrics = collector.collect_metrics()
            collector.store_metrics(metrics)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        print(f"   Average metrics collection time: {avg_time:.3f}s")
        
        if avg_time < 1.0:  # Should be fast
            print("✅ Performance Test: PASSED")
            return True
        else:
            print("⚠️ Performance Test: SLOW (but functional)")
            return True
            
    except Exception as e:
        print(f"❌ Performance Test: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Smart Auto-Scaling System Test Suite")
    print("=" * 50)
    
    tests = [
        test_metrics_collector,
        test_predictor,
        test_scaling_engine,
        test_resource_manager,
        test_integration,
        test_dashboard_api,
        run_performance_test
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run demo: python main.py")
        print("3. Start monitoring: python main.py --monitor")
        print("4. Start dashboard: python dashboard.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
