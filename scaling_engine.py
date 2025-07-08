from typing import Dict, List
from datetime import datetime
import json
import os

class ScalingEngine:
    """Makes intelligent scaling decisions based on predictions and current state"""
    
    def __init__(self, config_file: str = "scaling_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.decision_history = []
        
    def _load_config(self) -> Dict:
        """Load scaling configuration"""
        default_config = {
            "min_instances": 1,
            "max_instances": 10,
            "scale_up_threshold": 70,
            "scale_down_threshold": 30,
            "scale_up_cooldown": 300,  # 5 minutes in seconds
            "scale_down_cooldown": 600,  # 10 minutes in seconds
            "confidence_threshold": 0.6,
            "resource_limits": {
                "cpu_cores": 16,
                "memory_gb": 32,
                "storage_gb": 500
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    default_config.update(config)
            except:
                pass
        
        # Save config for reference
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def make_scaling_decision(self, 
                            current_state: Dict, 
                            recommendation: Dict, 
                            recent_decisions: List[Dict] = None) -> Dict:
        """Make final scaling decision considering all factors"""
        
        timestamp = datetime.now().isoformat()
        
        # Check cooldown periods
        cooldown_check = self._check_cooldown(recent_decisions or [])
        if not cooldown_check['allowed']:
            return {
                'timestamp': timestamp,
                'action': 'maintain',
                'reason': f"Cooldown active: {cooldown_check['reason']}",
                'confidence': 1.0,
                'recommended_instances': current_state.get('current_instances', 1),
                'recommended_resources': current_state.get('current_resources', {}),
                'cooldown_remaining': cooldown_check.get('remaining_time', 0)
            }
        
        # Check confidence threshold
        if recommendation['confidence'] < self.config['confidence_threshold']:
            return {
                'timestamp': timestamp,
                'action': 'maintain',
                'reason': f"Low confidence: {recommendation['confidence']:.2f}",
                'confidence': recommendation['confidence'],
                'recommended_instances': current_state.get('current_instances', 1),
                'recommended_resources': current_state.get('current_resources', {})
            }
        
        # Calculate target instances and resources
        target_instances, target_resources = self._calculate_target_resources(
            current_state, recommendation
        )
        
        # Validate against limits
        target_instances = max(self.config['min_instances'], 
                             min(self.config['max_instances'], target_instances))
        
        # Determine final action
        current_instances = current_state.get('current_instances', 1)
        
        if target_instances > current_instances:
            action = 'scale_up'
        elif target_instances < current_instances:
            action = 'scale_down'
        else:
            action = 'maintain'
        
        # Create decision
        decision = {
            'timestamp': timestamp,
            'action': action,
            'reason': self._generate_decision_reason(recommendation, target_instances, current_instances),
            'confidence': recommendation['confidence'],
            'current_instances': current_instances,
            'recommended_instances': target_instances,
            'current_resources': current_state.get('current_resources', {}),
            'recommended_resources': target_resources,
            'predicted_load': recommendation.get('predicted_load', 0),
            'max_predicted_load': recommendation.get('max_predicted_load', 0),
            'cost_impact': self._estimate_cost_impact(current_instances, target_instances)
        }
        
        return decision
    
    def _check_cooldown(self, recent_decisions: List[Dict]) -> Dict:
        """Check if scaling action is allowed based on cooldown periods"""
        if not recent_decisions:
            return {'allowed': True}
        
        current_time = datetime.now()
        
        for decision in reversed(recent_decisions[-10:]):  # Check last 10 decisions
            decision_time = datetime.fromisoformat(decision['timestamp'])
            time_diff = (current_time - decision_time).total_seconds()
            
            if decision['action'] == 'scale_up':
                if time_diff < self.config['scale_up_cooldown']:
                    remaining = self.config['scale_up_cooldown'] - time_diff
                    return {
                        'allowed': False,
                        'reason': f"Scale-up cooldown active",
                        'remaining_time': remaining
                    }
            
            elif decision['action'] == 'scale_down':
                if time_diff < self.config['scale_down_cooldown']:
                    remaining = self.config['scale_down_cooldown'] - time_diff
                    return {
                        'allowed': False,
                        'reason': f"Scale-down cooldown active",
                        'remaining_time': remaining
                    }
        
        return {'allowed': True}
    
    def _calculate_target_resources(self, current_state: Dict, recommendation: Dict) -> tuple:
        """Calculate target instances and resource allocation"""
        current_instances = current_state.get('current_instances', 1)
        current_load = current_state.get('load_score', 50)
        predicted_load = recommendation.get('max_predicted_load', current_load)
        
        # Simple scaling algorithm based on load
        if recommendation['action'] == 'scale_up':
            # Scale up: add instances based on predicted load
            load_factor = predicted_load / 100
            additional_instances = max(1, int(load_factor * 2))
            target_instances = current_instances + additional_instances
            
        elif recommendation['action'] == 'scale_down':
            # Scale down: remove instances if load is low
            if predicted_load < 20:
                target_instances = max(1, current_instances - 2)
            elif predicted_load < 40:
                target_instances = max(1, current_instances - 1)
            else:
                target_instances = current_instances
        else:
            target_instances = current_instances
        
        # Calculate resource allocation per instance
        target_resources = self._calculate_resource_allocation(target_instances, predicted_load)
        
        return target_instances, target_resources
    
    def _calculate_resource_allocation(self, instances: int, predicted_load: float) -> Dict:
        """Calculate optimal resource allocation"""
        load_factor = predicted_load / 100
        
        # Base resources per instance
        base_cpu = 2
        base_memory = 4
        base_storage = 20
        
        # Adjust based on load
        cpu_per_instance = base_cpu + (load_factor * 2)
        memory_per_instance = base_memory + (load_factor * 4)
        storage_per_instance = base_storage + (load_factor * 10)
        
        total_resources = {
            'total_cpu_cores': min(self.config['resource_limits']['cpu_cores'], 
                                 instances * cpu_per_instance),
            'total_memory_gb': min(self.config['resource_limits']['memory_gb'], 
                                 instances * memory_per_instance),
            'total_storage_gb': min(self.config['resource_limits']['storage_gb'], 
                                  instances * storage_per_instance),
            'cpu_per_instance': cpu_per_instance,
            'memory_per_instance': memory_per_instance,
            'storage_per_instance': storage_per_instance
        }
        
        return total_resources
    
    def _generate_decision_reason(self, recommendation: Dict, target: int, current: int) -> str:
        """Generate human-readable reason for scaling decision"""
        base_reason = recommendation['reason']
        
        if target > current:
            return f"Scaling up from {current} to {target} instances: {base_reason}"
        elif target < current:
            return f"Scaling down from {current} to {target} instances: {base_reason}"
        else:
            return f"Maintaining {current} instances: {base_reason}"
    
    def _estimate_cost_impact(self, current_instances: int, target_instances: int) -> Dict:
        """Estimate cost impact of scaling decision"""
        # Simplified cost calculation (per instance per hour)
        cost_per_instance_hour = 0.10  # $0.10 per instance per hour
        
        current_cost = current_instances * cost_per_instance_hour
        target_cost = target_instances * cost_per_instance_hour
        cost_change = target_cost - current_cost
        
        return {
            'current_hourly_cost': round(current_cost, 2),
            'target_hourly_cost': round(target_cost, 2),
            'hourly_cost_change': round(cost_change, 2),
            'daily_cost_change': round(cost_change * 24, 2),
            'monthly_cost_change': round(cost_change * 24 * 30, 2)
        }
    
    def evaluate_scaling_effectiveness(self, 
                                     decision: Dict, 
                                     actual_metrics: List[Dict]) -> Dict:
        """Evaluate how effective a previous scaling decision was"""
        if not actual_metrics:
            return {'effectiveness': 'unknown', 'score': 0.5}
        
        predicted_load = decision.get('predicted_load', 50)
        actual_loads = [m['load_score'] for m in actual_metrics]
        avg_actual_load = sum(actual_loads) / len(actual_loads)
        
        # Calculate prediction accuracy
        prediction_error = abs(predicted_load - avg_actual_load)
        accuracy_score = max(0, 1 - (prediction_error / 100))
        
        # Evaluate if scaling was appropriate
        action = decision['action']
        effectiveness_score = 0.5
        
        if action == 'scale_up':
            if avg_actual_load > 70:
                effectiveness_score = 0.9  # Good decision
            elif avg_actual_load > 50:
                effectiveness_score = 0.7  # Reasonable decision
            else:
                effectiveness_score = 0.3  # May have been premature
        
        elif action == 'scale_down':
            if avg_actual_load < 30:
                effectiveness_score = 0.9  # Good decision
            elif avg_actual_load < 50:
                effectiveness_score = 0.7  # Reasonable decision
            else:
                effectiveness_score = 0.3  # May have been too aggressive
        
        else:  # maintain
            if 30 <= avg_actual_load <= 70:
                effectiveness_score = 0.8  # Good decision to maintain
            else:
                effectiveness_score = 0.4  # Maybe should have acted
        
        overall_score = (accuracy_score + effectiveness_score) / 2
        
        return {
            'effectiveness': 'excellent' if overall_score > 0.8 else 
                           'good' if overall_score > 0.6 else 
                           'fair' if overall_score > 0.4 else 'poor',
            'score': round(overall_score, 2),
            'prediction_accuracy': round(accuracy_score, 2),
            'decision_appropriateness': round(effectiveness_score, 2),
            'predicted_load': predicted_load,
            'actual_avg_load': round(avg_actual_load, 2),
            'prediction_error': round(prediction_error, 2)
        }

if __name__ == "__main__":
    # Test the scaling engine
    engine = ScalingEngine()
    
    # Mock current state
    current_state = {
        'current_instances': 2,
        'load_score': 75,
        'current_resources': {
            'total_cpu_cores': 4,
            'total_memory_gb': 8
        }
    }
    
    # Mock recommendation
    recommendation = {
        'action': 'scale_up',
        'confidence': 0.8,
        'predicted_load': 85,
        'max_predicted_load': 90,
        'reason': 'High load predicted'
    }
    
    # Make decision
    decision = engine.make_scaling_decision(current_state, recommendation)
    print("Scaling Decision:", json.dumps(decision, indent=2))
