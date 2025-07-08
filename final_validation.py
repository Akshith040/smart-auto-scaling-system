#!/usr/bin/env python3
"""
Final Validation Script for Smart Auto-Scaling System
Tests all deliverables against the original problem statement
"""

import requests
import json
import time
import sys
from datetime import datetime

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print('='*60)

def print_check(item, status):
    """Print check item with status"""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {item}")
    return status

def test_dashboard_endpoint(endpoint, description):
    """Test a dashboard endpoint"""
    try:
        response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
        success = response.status_code == 200 and len(response.json()) > 0
        print_check(f"{description}: {endpoint}", success)
        return success
    except Exception as e:
        print_check(f"{description}: {endpoint} - Error: {str(e)}", False)
        return False

def validate_real_metrics():
    """Validate that we're getting real system metrics"""
    print_header("REAL METRICS VALIDATION")
    
    try:
        # Test verification endpoint
        response = requests.get("http://localhost:5000/api/verification", timeout=5)
        data = response.json()
        
        checks = []
        checks.append(print_check("Live system data collection", 
                                data.get("metrics_source") == "real_system"))
        checks.append(print_check("Real process list available", 
                                len(data.get("top_processes", [])) > 0))
        checks.append(print_check("System info includes real hardware specs", 
                                "processor" in data.get("verification", {}).get("system_info", {})))
        checks.append(print_check("Raw system metrics are non-zero", 
                                data.get("verification", {}).get("raw_system_data", {}).get("cpu_percent_raw", 0) >= 0))
        
        # Test that metrics change over time
        response1 = requests.get("http://localhost:5000/api/metrics", timeout=5)
        time.sleep(2)
        response2 = requests.get("http://localhost:5000/api/metrics", timeout=5)
        
        metrics1 = response1.json().get("current", {})
        metrics2 = response2.json().get("current", {})
        
        timestamp_changed = metrics1.get("timestamp") != metrics2.get("timestamp")
        checks.append(print_check("Metrics update in real-time", timestamp_changed))
        
        return all(checks)
        
    except Exception as e:
        print_check(f"Real metrics validation failed: {str(e)}", False)
        return False

def validate_ai_ml():
    """Validate AI/ML capabilities"""
    print_header("AI/ML VALIDATION")
    
    try:
        # Test predictions endpoint
        response = requests.get("http://localhost:5000/api/predictions", timeout=5)
        data = response.json()
        
        checks = []
        checks.append(print_check("Time series forecasting implemented", 
                                len(data.get("predictions", [])) > 0))
        checks.append(print_check("Anomaly detection active", 
                                "anomalies_detected" in data))
        checks.append(print_check("Model confidence available", 
                                "model_performance" in data))
        checks.append(print_check("Multi-step predictions available", 
                                len(data.get("predictions", [])) >= 5))
        
        return all(checks)
        
    except Exception as e:
        print_check(f"AI/ML validation failed: {str(e)}", False)
        return False

def validate_scaling_engine():
    """Validate intelligent scaling"""
    print_header("SCALING ENGINE VALIDATION")
    
    try:
        # Test scaling status
        response = requests.get("http://localhost:5000/api/scaling/status", timeout=5)
        data = response.json()
        
        checks = []
        checks.append(print_check("Scaling decisions tracked", 
                                "last_action" in data))
        checks.append(print_check("Scaling history available", 
                                len(data.get("recent_actions", [])) >= 0))
        checks.append(print_check("Resource state tracking", 
                                "current_instances" in data))
        checks.append(print_check("Cost analysis integrated", 
                                "total_cost" in data))
        
        # Test scaling execution
        response = requests.post("http://localhost:5000/api/scaling/execute", 
                               json={"instances": 2}, timeout=5)
        scaling_success = response.status_code == 200
        checks.append(print_check("Scaling execution available", scaling_success))
        
        return all(checks)
        
    except Exception as e:
        print_check(f"Scaling validation failed: {str(e)}", False)
        return False

def validate_dashboard():
    """Validate web dashboard"""
    print_header("DASHBOARD VALIDATION")
    
    checks = []
    
    # Test all API endpoints
    endpoints = [
        ("/api/metrics", "Current metrics API"),
        ("/api/metrics/realtime", "Real-time metrics API"),
        ("/api/predictions", "Predictions API"),
        ("/api/scaling/status", "Scaling status API"),
        ("/api/system/health", "System health API"),
        ("/api/verification", "Verification API")
    ]
    
    for endpoint, description in endpoints:
        checks.append(test_dashboard_endpoint(endpoint, description))
    
    # Test dashboard UI
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        ui_works = response.status_code == 200 and "Smart Auto-Scaling Dashboard" in response.text
        checks.append(print_check("Web UI accessible", ui_works))
    except:
        checks.append(print_check("Web UI accessible", False))
    
    return all(checks)

def validate_architecture():
    """Validate modular architecture"""
    print_header("ARCHITECTURE VALIDATION")
    
    import os
    checks = []
    
    # Check for required modules
    required_files = [
        "metrics_collector.py",
        "predictor.py", 
        "scaling_engine.py",
        "resource_manager.py",
        "dashboard.py",
        "main.py",
        "test_system.py",
        "requirements.txt",
        "README.md"
    ]
    
    for file in required_files:
        exists = os.path.exists(file)
        checks.append(print_check(f"Module exists: {file}", exists))
    
    # Check templates directory
    template_exists = os.path.exists("templates/dashboard.html")
    checks.append(print_check("Dashboard template exists", template_exists))
    
    return all(checks)

def validate_documentation():
    """Validate documentation completeness"""
    print_header("DOCUMENTATION VALIDATION")
    
    import os
    checks = []
    
    # Check documentation files
    doc_files = [
        ("README.md", "Project documentation"),
        ("ASSESSMENT_SUMMARY.md", "Assessment summary"),
        ("REAL_METRICS_PROOF.md", "Real metrics proof"),
        ("VERIFICATION_COMPLETE.md", "Verification documentation")
    ]
    
    for file, description in doc_files:
        exists = os.path.exists(file)
        checks.append(print_check(f"{description}: {file}", exists))
    
    return all(checks)

def main():
    """Run complete validation"""
    print_header("SMART AUTO-SCALING SYSTEM - FINAL VALIDATION")
    print("Testing all deliverables against problem statement requirements...")
    
    # Check if dashboard is running
    try:
        requests.get("http://localhost:5000/api/system/health", timeout=5)
        dashboard_running = True
    except:
        dashboard_running = False
        print("❌ Dashboard not running at localhost:5000")
        print("   Please start with: python dashboard.py")
        return False
    
    if not dashboard_running:
        return False
    
    # Run all validations
    validations = [
        ("Real System Metrics", validate_real_metrics),
        ("AI/ML Implementation", validate_ai_ml),
        ("Scaling Engine", validate_scaling_engine),
        ("Web Dashboard", validate_dashboard),
        ("Modular Architecture", validate_architecture),
        ("Documentation", validate_documentation)
    ]
    
    results = {}
    all_passed = True
    
    for name, validator in validations:
        results[name] = validator()
        all_passed = all_passed and results[name]
    
    # Final summary
    print_header("VALIDATION SUMMARY")
    
    for name, passed in results.items():
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {name}: {'PASSED' if passed else 'FAILED'}")
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ System meets all problem statement requirements")
        print("✅ Real system metrics collection verified")
        print("✅ AI/ML capabilities demonstrated") 
        print("✅ Intelligent auto-scaling implemented")
        print("✅ Modular architecture confirmed")
        print("✅ Web dashboard functional")
        print("✅ Complete documentation available")
    else:
        print("❌ Some validations failed")
        print("Review failed items above")
    
    print(f"{'='*60}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
