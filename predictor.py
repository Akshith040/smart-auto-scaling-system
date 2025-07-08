import numpy as np
import pandas as pd
import time
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

class DemandPredictor:
    """Time series forecasting and anomaly detection for demand prediction"""
    
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = MinMaxScaler()
        self.is_trained = False
        self.anomaly_threshold = 2.0  # Standard deviations for anomaly detection
        self.feature_columns = []  # Will be set during training
        
    def prepare_time_series_data(self, metrics: List[Dict], target_column: str = 'load_score') -> Tuple[np.ndarray, np.ndarray]:
        """Prepare time series data for training"""
        if len(metrics) < 10:
            return np.array([]), np.array([])
        
        df = pd.DataFrame(metrics)
        
        # Convert timestamp to numeric features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['minute'] = df['timestamp'].dt.minute
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Create lag features (previous values) - only if sufficient data
        lag_features = []
        for lag in [1, 2, 3]:
            if len(df) > lag + 5:  # Ensure enough data after lag
                col_name = f'{target_column}_lag_{lag}'
                df[col_name] = df[target_column].shift(lag)
                lag_features.append(col_name)
        
        # Create rolling averages - only if sufficient data
        rolling_features = []
        for window in [3, 5]:
            if len(df) > window + 5:  # Ensure enough data after rolling
                col_name = f'{target_column}_rolling_{window}'
                df[col_name] = df[target_column].rolling(window=window).mean()
                rolling_features.append(col_name)
        
        # Drop rows with NaN values
        df = df.dropna()
        
        if len(df) < 5:
            return np.array([]), np.array([])
        
        # Define consistent feature set - ALWAYS use the same features
        self.feature_columns = ['hour', 'minute', 'day_of_week', 'cpu_percent', 'memory_percent', 'response_time_ms']
        
        # Add only the lag and rolling features that were successfully created
        self.feature_columns.extend(lag_features)
        self.feature_columns.extend(rolling_features)
        
        # Ensure all features exist in the dataframe
        available_features = [col for col in self.feature_columns if col in df.columns]
        self.feature_columns = available_features
        
        X = df[self.feature_columns].values
        y = df[target_column].values
        
        return X, np.array(y)
    
    def train_model(self, metrics: List[Dict]) -> bool:
        """Train the forecasting model"""
        X, y = self.prepare_time_series_data(metrics)
        
        if len(X) == 0:
            return False
        
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            # Calculate training accuracy
            y_pred = self.model.predict(X_scaled)
            mse = mean_squared_error(y, y_pred)
            print(f"Model trained successfully. MSE: {mse:.2f}")
            
            return True
        except Exception as e:
            print(f"Training failed: {e}")
            return False
    
    def predict_demand(self, recent_metrics: List[Dict], horizon: int = 5) -> List[float]:
        """Predict future demand for the next 'horizon' time steps"""
        if not self.is_trained or len(recent_metrics) < 5:
            # Return current load as prediction if model not ready
            current_load = recent_metrics[-1]['load_score'] if recent_metrics else 50.0
            return [current_load] * horizon
        
        predictions = []
        
        try:
            # Use the most recent metrics as base for prediction
            last_metrics = recent_metrics[-15:]  # Use last 15 data points
            
            for step in range(horizon):
                # Prepare data using the same feature set as training
                df = pd.DataFrame(last_metrics)
                
                # Convert timestamp to numeric features
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.hour
                df['minute'] = df['timestamp'].dt.minute
                df['day_of_week'] = df['timestamp'].dt.dayofweek
                
                # Create the same lag and rolling features as training
                for feature in self.feature_columns:
                    if 'lag_' in feature:
                        lag_num = int(feature.split('_')[-1])
                        target_col = feature.replace(f'_lag_{lag_num}', '')
                        if len(df) > lag_num:
                            df[feature] = df[target_col].shift(lag_num)
                    elif 'rolling_' in feature:
                        window_num = int(feature.split('_')[-1])
                        target_col = feature.replace(f'_rolling_{window_num}', '')
                        if len(df) > window_num:
                            df[feature] = df[target_col].rolling(window=window_num).mean()
                
                # Drop NaN and get the most recent complete row
                df = df.dropna()
                
                if len(df) == 0:
                    predictions.append(recent_metrics[-1]['load_score'])
                    continue
                
                # Extract features for prediction
                try:
                    feature_values = []
                    for feature in self.feature_columns:
                        if feature in df.columns:
                            feature_values.append(df[feature].iloc[-1])
                        else:
                            # Fallback value if feature doesn't exist
                            feature_values.append(0.0)
                    
                    X_pred = np.array([feature_values])
                    
                    # Scale and predict
                    X_scaled = self.scaler.transform(X_pred)
                    prediction = self.model.predict(X_scaled)[0]
                    
                    # Ensure prediction is within reasonable bounds
                    prediction = max(0, min(100, prediction))
                    predictions.append(prediction)
                    
                    # Create synthetic next data point for multi-step prediction
                    synthetic_metric = self._create_synthetic_metric(last_metrics[-1], prediction)
                    last_metrics.append(synthetic_metric)
                
                except Exception as e:
                    print(f"Prediction step {step} failed: {e}")
                    predictions.append(recent_metrics[-1]['load_score'])
        
        except Exception as e:
            print(f"Prediction failed: {e}")
            # Fallback to trend-based prediction
            predictions = self._simple_trend_prediction(recent_metrics, horizon)
        
        return predictions
    
    def _create_synthetic_metric(self, last_metric: Dict, predicted_load: float) -> Dict:
        """Create synthetic metric for multi-step prediction"""
        import copy
        from datetime import datetime, timedelta
        
        synthetic = copy.deepcopy(last_metric)
        
        # Update timestamp
        last_time = pd.to_datetime(last_metric['timestamp'])
        synthetic['timestamp'] = (last_time + timedelta(minutes=1)).isoformat()
        
        # Update load score with prediction
        synthetic['load_score'] = predicted_load
        
        # Estimate other metrics based on load score
        load_factor = predicted_load / 100
        synthetic['cpu_percent'] = min(100, load_factor * 80)
        synthetic['memory_percent'] = min(100, load_factor * 70)
        synthetic['response_time_ms'] = 50 + (load_factor * 150)
        
        return synthetic
    
    def _simple_trend_prediction(self, recent_metrics: List[Dict], horizon: int) -> List[float]:
        """Simple trend-based prediction as fallback"""
        if len(recent_metrics) < 2:
            return [50.0] * horizon
        
        # Calculate simple trend
        loads = [m['load_score'] for m in recent_metrics[-10:]]
        trend = (loads[-1] - loads[0]) / len(loads) if len(loads) > 1 else 0
        
        predictions = []
        current_load = loads[-1]
        
        for i in range(horizon):
            next_load = current_load + (trend * (i + 1))
            next_load = max(0, min(100, next_load))  # Bound between 0-100
            predictions.append(next_load)
        
        return predictions
    
    def detect_anomalies(self, recent_metrics: List[Dict], window_size: int = 20) -> List[bool]:
        """Detect anomalies in recent metrics using statistical method"""
        if len(recent_metrics) < window_size:
            return [False] * len(recent_metrics)
        
        loads = [m['load_score'] for m in recent_metrics]
        anomalies = []
        
        for i in range(len(loads)):
            if i < window_size:
                anomalies.append(False)
                continue
            
            # Use rolling window for anomaly detection
            window = loads[i-window_size:i]
            mean_val = np.mean(window)
            std_val = np.std(window)
            
            # Check if current value is anomalous
            if std_val > 0:
                z_score = abs(loads[i] - mean_val) / std_val
                is_anomaly = z_score > self.anomaly_threshold
            else:
                is_anomaly = False
            
            anomalies.append(is_anomaly)
        
        return anomalies
    
    def get_scaling_recommendation(self, predictions: List[float], current_load: float) -> Dict:
        """Generate scaling recommendations based on predictions"""
        if not predictions:
            return {'action': 'maintain', 'confidence': 0.5, 'reason': 'No predictions available'}
        
        avg_predicted_load = sum(predictions) / len(predictions)
        max_predicted_load = max(predictions)
        trend = predictions[-1] - current_load if predictions else 0
        
        # Scaling decision logic
        if max_predicted_load > 80:
            action = 'scale_up'
            confidence = min(0.9, (max_predicted_load - 80) / 20)
            reason = f"High load predicted: {max_predicted_load:.1f}%"
        elif avg_predicted_load < 30 and current_load < 40:
            action = 'scale_down'
            confidence = min(0.8, (40 - avg_predicted_load) / 40)
            reason = f"Low load predicted: {avg_predicted_load:.1f}%"
        elif trend > 15:
            action = 'scale_up'
            confidence = 0.7
            reason = f"Rising trend detected: +{trend:.1f}%"
        elif trend < -15:
            action = 'scale_down'
            confidence = 0.6
            reason = f"Declining trend detected: {trend:.1f}%"
        else:
            action = 'maintain'
            confidence = 0.8
            reason = f"Stable load predicted: {avg_predicted_load:.1f}%"
        
        return {
            'action': action,
            'confidence': confidence,
            'reason': reason,
            'predicted_load': avg_predicted_load,
            'max_predicted_load': max_predicted_load,
            'trend': trend
        }

if __name__ == "__main__":
    # Test the predictor
    from metrics_collector import MetricsCollector
    
    collector = MetricsCollector()
    predictor = DemandPredictor()
    
    # Collect some sample data
    print("Collecting sample data...")
    for i in range(20):
        metrics = collector.collect_metrics()
        collector.store_metrics(metrics)
        time.sleep(0.1)  # Fast sampling for demo
    
    recent_metrics = collector.get_recent_metrics(20)
    
    # Train model
    print("Training prediction model...")
    success = predictor.train_model(recent_metrics)
    
    if success:
        # Make predictions
        predictions = predictor.predict_demand(recent_metrics, horizon=5)
        print(f"Predictions: {predictions}")
        
        # Detect anomalies
        anomalies = predictor.detect_anomalies(recent_metrics)
        print(f"Anomalies detected: {sum(anomalies)} out of {len(anomalies)}")
        
        # Get scaling recommendation
        current_load = recent_metrics[-1]['load_score']
        recommendation = predictor.get_scaling_recommendation(predictions, current_load)
        print(f"Scaling recommendation: {recommendation}")
    else:
        print("Model training failed")
