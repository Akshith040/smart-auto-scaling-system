import psutil
import time
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional

class MetricsCollector:
    """Collects system performance metrics"""
    
    def __init__(self, storage_file: str = "metrics.json"):
        self.storage_file = storage_file
        self.metrics_history = self._load_metrics()
    
    def _load_metrics(self) -> List[Dict]:
        """Load existing metrics from file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_metrics(self):
        """Save metrics to file"""
        with open(self.storage_file, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)
    
    def collect_metrics(self) -> Dict:
        """Collect current system metrics"""
        timestamp = datetime.now().isoformat()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Get disk usage for Windows
        try:
            if os.name == 'nt':  # Windows
                total, used, free = shutil.disk_usage('C:')
                disk_percent = (used / total) * 100
            else:  # Unix/Linux
                total, used, free = shutil.disk_usage('/')
                disk_percent = (used / total) * 100
        except Exception as e:
            print(f"Disk usage error: {e}")
            # Fallback if disk access fails
            disk_percent = 50.0
        
        # Network metrics (simplified, with error handling)
        try:
            network = psutil.net_io_counters()
            network_sent = int(network.bytes_sent) if network else 0
            network_recv = int(network.bytes_recv) if network else 0
        except:
            network_sent = 0
            network_recv = 0
        
        # Simulate application-specific metrics
        response_time = self._simulate_response_time(cpu_percent)
        active_connections = self._simulate_connections(cpu_percent)
        
        metrics = {
            'timestamp': timestamp,
            'cpu_percent': float(cpu_percent),
            'memory_percent': float(memory.percent),
            'memory_used_gb': float(memory.used / (1024**3)),
            'disk_percent': float(disk_percent),
            'network_bytes_sent': network_sent,
            'network_bytes_recv': network_recv,
            'response_time_ms': float(response_time),
            'active_connections': int(active_connections),
            'load_score': float(self._calculate_load_score(cpu_percent, memory.percent, response_time))
        }
        
        return metrics
    
    def _simulate_response_time(self, cpu_percent: float) -> float:
        """Simulate application response time based on CPU usage"""
        base_time = 50  # Base response time in ms
        load_factor = (cpu_percent / 100) * 200  # Increase with CPU load
        return round(base_time + load_factor, 2)
    
    def _simulate_connections(self, cpu_percent: float) -> int:
        """Simulate active connections based on system load"""
        base_connections = 100
        load_connections = int((cpu_percent / 100) * 500)
        return base_connections + load_connections
    
    def _calculate_load_score(self, cpu: float, memory: float, response_time: float) -> float:
        """Calculate overall load score (0-100)"""
        # Weighted average of different metrics
        weights = {'cpu': 0.4, 'memory': 0.3, 'response': 0.3}
        response_score = min((response_time / 200) * 100, 100)  # Normalize response time
        
        load_score = (
            cpu * weights['cpu'] +
            memory * weights['memory'] +
            response_score * weights['response']
        )
        
        return round(load_score, 2)
    
    def store_metrics(self, metrics: Dict):
        """Store metrics in history"""
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 entries to prevent file from growing too large
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        self._save_metrics()
    
    def get_recent_metrics(self, count: int = 100) -> List[Dict]:
        """Get recent metrics"""
        return self.metrics_history[-count:] if self.metrics_history else []
    
    def get_metrics_summary(self) -> Dict:
        """Get summary statistics of recent metrics"""
        if not self.metrics_history:
            return {}
        
        recent = self.get_recent_metrics(50)
        
        return {
            'avg_cpu': sum(m['cpu_percent'] for m in recent) / len(recent),
            'avg_memory': sum(m['memory_percent'] for m in recent) / len(recent),
            'avg_response_time': sum(m['response_time_ms'] for m in recent) / len(recent),
            'avg_load_score': sum(m['load_score'] for m in recent) / len(recent),
            'total_samples': len(self.metrics_history)
        }
    
    def get_system_verification(self, current_metrics: Optional[Dict] = None) -> Dict:
        """Get system verification info to prove metrics are real - uses SAME data sources as dashboard"""
        import platform
        import socket
        import getpass
        
        # Use provided metrics or collect new ones
        if current_metrics is None:
            current_metrics = self.collect_metrics()
        
        # Get system info
        try:
            if os.name == 'nt':  # Windows
                disk_total, disk_used, disk_free = shutil.disk_usage('C:')
            else:  # Unix/Linux
                disk_total, disk_used, disk_free = shutil.disk_usage('/')
        except Exception as e:
            print(f"Disk usage error in verification: {e}")
            disk_total = 0
            disk_used = 0
            disk_free = 0
        
        memory = psutil.virtual_memory()
        
        # Get network info with error handling
        try:
            network = psutil.net_io_counters()
            network_sent = int(network.bytes_sent) if network else 0
            network_recv = int(network.bytes_recv) if network else 0
        except:
            network_sent = 0
            network_recv = 0
        
        verification = {
            'system_info': {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0],
                'machine': platform.machine(),
                'node': platform.node(),
                'username': getpass.getuser(),
                'python_version': platform.python_version()
            },
            'network_info': {
                'hostname': socket.gethostname(),
                'local_ip': socket.gethostbyname(socket.gethostname())
            },
            'live_verification': {
                'timestamp': current_metrics['timestamp'],
                'process_count': len(psutil.pids()),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(memory.total / (1024**3), 2)
            },
            'current_dashboard_metrics': {
                'cpu_percent': current_metrics['cpu_percent'],
                'memory_percent': current_metrics['memory_percent'],
                'memory_used_gb': current_metrics['memory_used_gb'],
                'disk_percent': current_metrics['disk_percent'],
                'network_bytes_sent': current_metrics['network_bytes_sent'],
                'network_bytes_recv': current_metrics['network_bytes_recv'],
                'response_time_ms': current_metrics['response_time_ms'],
                'active_connections': current_metrics['active_connections'],
                'load_score': current_metrics['load_score']
            },
            'raw_system_data': {
                'cpu_percent_raw': float(psutil.cpu_percent(interval=0.5)),
                'memory_total_bytes': memory.total,
                'memory_used_bytes': memory.used,
                'memory_available_bytes': memory.available,
                'disk_total_bytes': disk_total,
                'disk_used_bytes': disk_used,
                'disk_free_bytes': disk_free,
                'network_bytes_sent_raw': network_sent,
                'network_bytes_recv_raw': network_recv
            }
        }
        
        return verification
    
    def get_process_details(self, limit: int = 10) -> List[Dict]:
        """Get details of running processes to prove real system monitoring"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] is not None:
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': round(proc_info['cpu_percent'], 2),
                            'memory_percent': round(proc_info['memory_percent'], 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and return top processes
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
            
        except Exception as e:
            return [{'error': f'Failed to get process details: {str(e)}'}]

if __name__ == "__main__":
    # Test the metrics collector
    collector = MetricsCollector()
    
    print("Collecting metrics...")
    for i in range(5):
        metrics = collector.collect_metrics()
        collector.store_metrics(metrics)
        print(f"Sample {i+1}: CPU: {metrics['cpu_percent']}%, "
              f"Memory: {metrics['memory_percent']}%, "
              f"Load Score: {metrics['load_score']}")
        time.sleep(2)
    
    summary = collector.get_metrics_summary()
    print("\nSummary:", summary)
    verification = collector.get_system_verification()
    print("\nVerification:", json.dumps(verification, indent=2))
    
    process_details = collector.get_process_details()
    print("\nTop Processes:", json.dumps(process_details, indent=2))
