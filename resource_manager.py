import time
import json
import os
import psutil
import shutil
from typing import Dict, List
from datetime import datetime

class ResourceManager:
    """Executes scaling decisions and manages resources"""
    
    def __init__(self, state_file: str = "resource_state.json", metrics_collector=None):
        self.state_file = state_file
        self.metrics_collector = metrics_collector
        self.current_state = self._load_state()
        self.execution_history = []
        
    def _load_state(self) -> Dict:
        """Load current resource state"""
        # Get real system specifications
        memory_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        cpu_cores = psutil.cpu_count()
        
        # Get disk space for system drive
        try:
            if os.name == 'nt':  # Windows
                total, used, free = shutil.disk_usage('C:')
                storage_gb = round(total / (1024**3), 1)
            else:  # Unix/Linux
                total, used, free = shutil.disk_usage('/')
                storage_gb = round(total / (1024**3), 1)
        except Exception as e:
            print(f"Disk usage error: {e}")
            storage_gb = 500  # Reasonable fallback
        
        default_state = {
            'instances': 1,
            'resources': {
                'total_cpu_cores': cpu_cores,
                'total_memory_gb': memory_gb,
                'total_storage_gb': storage_gb,
                'cpu_per_instance': cpu_cores,
                'memory_per_instance': memory_gb,
                'storage_per_instance': storage_gb
            },
            'status': 'active',
            'last_updated': datetime.now().isoformat(),
            'scaling_events': []
        }
        
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    default_state.update(state)
            except:
                pass
        
        return default_state
    
    def _save_state(self):
        """Save current state to file"""
        self.current_state['last_updated'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.current_state, f, indent=2)
    
    def execute_scaling_decision(self, decision: Dict) -> Dict:
        """Execute a scaling decision and return execution result"""
        timestamp = datetime.now().isoformat()
        
        # Simulate scaling execution time
        execution_time = self._simulate_scaling_time(decision['action'])
        
        execution_result = {
            'timestamp': timestamp,
            'decision_id': id(decision),
            'action': decision['action'],
            'status': 'started',
            'execution_time_seconds': execution_time,
            'previous_state': dict(self.current_state),
            'errors': [],
            'warnings': []
        }
        
        try:
            if decision['action'] == 'scale_up':
                result = self._scale_up(decision)
            elif decision['action'] == 'scale_down':
                result = self._scale_down(decision)
            else:  # maintain
                result = self._maintain_resources(decision)
            
            execution_result.update(result)
            execution_result['status'] = 'completed'
            
            # Update state
            self._update_state(decision, execution_result)
            
        except Exception as e:
            execution_result['status'] = 'failed'
            execution_result['errors'].append(str(e))
            print(f"Scaling execution failed: {e}")
        
        # Log execution
        self.execution_history.append(execution_result)
        self._save_state()
        
        return execution_result
    
    def _scale_up(self, decision: Dict) -> Dict:
        """Execute scale-up operation"""
        current_instances = self.current_state['instances']
        target_instances = decision['recommended_instances']
        new_instances = target_instances - current_instances
        
        print(f"Scaling up: Adding {new_instances} instances...")
        
        # Simulate instance provisioning
        provisioned_instances = []
        for i in range(new_instances):
            instance_id = f"instance-{current_instances + i + 1}"
            
            # Simulate provisioning steps
            steps = [
                "Requesting compute resources",
                "Allocating CPU and memory",
                "Setting up networking",
                "Installing application",
                "Running health checks",
                "Adding to load balancer"
            ]
            
            for step in steps:
                print(f"  {instance_id}: {step}...")
                time.sleep(0.2)  # Simulate time
            
            provisioned_instances.append({
                'id': instance_id,
                'cpu_cores': decision['recommended_resources']['cpu_per_instance'],
                'memory_gb': decision['recommended_resources']['memory_per_instance'],
                'storage_gb': decision['recommended_resources']['storage_per_instance'],
                'status': 'active'
            })
        
        return {
            'instances_added': new_instances,
            'new_total_instances': target_instances,
            'provisioned_instances': provisioned_instances,
            'resource_allocation': decision['recommended_resources']
        }
    
    def _scale_down(self, decision: Dict) -> Dict:
        """Execute scale-down operation"""
        current_instances = self.current_state['instances']
        target_instances = decision['recommended_instances']
        instances_to_remove = current_instances - target_instances
        
        print(f"Scaling down: Removing {instances_to_remove} instances...")
        
        # Simulate graceful shutdown
        removed_instances = []
        for i in range(instances_to_remove):
            instance_id = f"instance-{current_instances - i}"
            
            # Simulate shutdown steps
            steps = [
                "Draining connections",
                "Removing from load balancer",
                "Stopping application",
                "Backing up data",
                "Deallocating resources"
            ]
            
            for step in steps:
                print(f"  {instance_id}: {step}...")
                time.sleep(0.1)  # Simulate time
            
            removed_instances.append({
                'id': instance_id,
                'status': 'terminated'
            })
        
        return {
            'instances_removed': instances_to_remove,
            'new_total_instances': target_instances,
            'removed_instances': removed_instances,
            'resource_allocation': decision['recommended_resources']
        }
    
    def _maintain_resources(self, decision: Dict) -> Dict:
        """Maintain current resources (no scaling)"""
        print("Maintaining current resource allocation...")
        
        # Simulate health checks and optimization
        checks = [
            "Performing health checks",
            "Optimizing resource allocation",
            "Updating monitoring configuration"
        ]
        
        for check in checks:
            print(f"  {check}...")
            time.sleep(0.1)
        
        return {
            'instances_maintained': self.current_state['instances'],
            'optimization_applied': True,
            'resource_allocation': self.current_state['resources']
        }
    
    def _update_state(self, decision: Dict, execution_result: Dict):
        """Update current resource state"""
        if execution_result['status'] == 'completed':
            if decision['action'] in ['scale_up', 'scale_down']:
                self.current_state['instances'] = decision['recommended_instances']
                self.current_state['resources'] = decision['recommended_resources']
            
            # Add scaling event to history
            scaling_event = {
                'timestamp': execution_result['timestamp'],
                'action': decision['action'],
                'instances_before': execution_result['previous_state']['instances'],
                'instances_after': self.current_state['instances'],
                'reason': decision['reason'],
                'execution_time': execution_result['execution_time_seconds']
            }
            
            self.current_state['scaling_events'].append(scaling_event)
            
            # Keep only last 50 events
            if len(self.current_state['scaling_events']) > 50:
                self.current_state['scaling_events'] = self.current_state['scaling_events'][-50:]
    
    def _simulate_scaling_time(self, action: str) -> float:
        """Simulate realistic scaling times"""
        if action == 'scale_up':
            return 2.0  # Scale up takes longer
        elif action == 'scale_down':
            return 1.0  # Scale down is faster
        else:
            return 0.5  # Maintenance is quick
    
    def get_current_state(self) -> Dict:
        """Get current resource state with additional metrics"""
        state = dict(self.current_state)
        
        # Add computed metrics
        state['utilization'] = self._calculate_utilization()
        state['cost_estimate'] = self._calculate_cost_estimate()
        state['uptime'] = self._calculate_uptime()
        
        return state
    
    def _calculate_utilization(self) -> Dict:
        """Calculate resource utilization based on real system metrics"""
        try:
            # Get real system metrics
            if self.metrics_collector:
                # Use metrics collector if available
                current_metrics = self.metrics_collector.collect_metrics()
                cpu_utilization = current_metrics['cpu_percent']
                memory_utilization = current_metrics['memory_percent']
                
                # Get network utilization from recent metrics
                recent_metrics = self.metrics_collector.get_recent_metrics(5)
                if recent_metrics:
                    # Calculate network utilization as percentage of recent activity
                    network_bytes = [m['network_bytes_sent'] + m['network_bytes_recv'] for m in recent_metrics]
                    if len(network_bytes) > 1:
                        # Calculate rate of change as utilization indicator
                        rate = (network_bytes[-1] - network_bytes[0]) / len(network_bytes)
                        network_utilization = min(100, max(0, rate / 1024 / 1024))  # MB/s as percentage
                    else:
                        network_utilization = 10.0
                else:
                    network_utilization = 10.0
                
                # Get disk utilization from current metrics
                disk_utilization = current_metrics['disk_percent']
                
            else:
                # Fallback to direct psutil calls
                cpu_utilization = psutil.cpu_percent(interval=1)
                memory_utilization = psutil.virtual_memory().percent
                
                # Get disk usage
                try:
                    if os.name == 'nt':  # Windows
                        total, used, free = shutil.disk_usage('C:')
                        disk_utilization = (used / total) * 100
                    else:  # Unix/Linux
                        total, used, free = shutil.disk_usage('/')
                        disk_utilization = (used / total) * 100
                except Exception as e:
                    print(f"Disk usage error: {e}")
                    disk_utilization = 50.0
                
                # Get network utilization
                try:
                    net_io = psutil.net_io_counters()
                    if net_io:
                        # Simple network activity indicator
                        total_bytes = net_io.bytes_sent + net_io.bytes_recv
                        network_utilization = min(50, (total_bytes / (1024**3)) * 10)  # Scale to percentage
                    else:
                        network_utilization = 5.0
                except:
                    network_utilization = 5.0
            
            return {
                'cpu_utilization_percent': round(cpu_utilization, 1),
                'memory_utilization_percent': round(memory_utilization, 1),
                'storage_utilization_percent': round(disk_utilization, 1),
                'network_utilization_percent': round(network_utilization, 1)
            }
            
        except Exception as e:
            print(f"Error calculating utilization: {e}")
            # Fallback to basic utilization
            return {
                'cpu_utilization_percent': 25.0,
                'memory_utilization_percent': 20.0,
                'storage_utilization_percent': 15.0,
                'network_utilization_percent': 10.0
            }
    
    def _calculate_cost_estimate(self) -> Dict:
        """Calculate current cost estimates"""
        instances = self.current_state['instances']
        cost_per_instance_hour = 0.10
        
        hourly_cost = instances * cost_per_instance_hour
        
        return {
            'hourly_cost': round(hourly_cost, 2),
            'daily_cost': round(hourly_cost * 24, 2),
            'monthly_cost': round(hourly_cost * 24 * 30, 2),
            'cost_per_instance': cost_per_instance_hour
        }
    
    def _calculate_uptime(self) -> Dict:
        """Calculate uptime statistics"""
        # Simplified uptime calculation
        total_events = len(self.current_state['scaling_events'])
        failed_events = len([e for e in self.execution_history if e.get('status') == 'failed'])
        
        success_rate = 1.0 if total_events == 0 else (total_events - failed_events) / total_events
        
        return {
            'success_rate_percent': round(success_rate * 100, 2),
            'total_scaling_events': total_events,
            'failed_events': failed_events,
            'current_status': self.current_state['status']
        }
    
    def get_scaling_history(self, limit: int = 20) -> List[Dict]:
        """Get recent scaling history"""
        return self.current_state['scaling_events'][-limit:]
    
    def rollback_last_scaling(self) -> Dict:
        """Rollback the last scaling operation"""
        if not self.current_state['scaling_events']:
            return {'status': 'failed', 'reason': 'No scaling events to rollback'}
        
        last_event = self.current_state['scaling_events'][-1]
        
        # Create rollback decision
        rollback_decision = {
            'action': 'rollback',
            'recommended_instances': last_event['instances_before'],
            'reason': f"Rollback of {last_event['action']} from {last_event['timestamp']}",
            'recommended_resources': {}  # Would need to store previous resources
        }
        
        print(f"Rolling back to {last_event['instances_before']} instances...")
        return self.execute_scaling_decision(rollback_decision)

if __name__ == "__main__":
    # Test the resource manager
    manager = ResourceManager()
    
    # Mock scaling decision
    decision = {
        'action': 'scale_up',
        'recommended_instances': 3,
        'recommended_resources': {
            'total_cpu_cores': 6,
            'total_memory_gb': 12,
            'total_storage_gb': 60,
            'cpu_per_instance': 2,
            'memory_per_instance': 4,
            'storage_per_instance': 20
        },
        'reason': 'Test scaling operation'
    }
    
    # Execute scaling
    result = manager.execute_scaling_decision(decision)
    print("\nExecution Result:", json.dumps(result, indent=2))
    
    # Get current state
    state = manager.get_current_state()
    print("\nCurrent State:", json.dumps(state, indent=2))
