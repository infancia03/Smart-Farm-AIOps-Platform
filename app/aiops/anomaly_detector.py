from sqlalchemy.orm import Session
from app.database import SensorData, Alert
from datetime import datetime, timedelta
from typing import List, Dict, Any
import statistics
import os
from dotenv import load_dotenv

load_dotenv()

class AnomalyDetector:
    """
    AIOps Anomaly Detection System
    Monitors sensor streams and detects anomalies in real-time
    """
    
    def __init__(self):
        # Load thresholds from environment
        self.temp_threshold = float(os.getenv("ANOMALY_THRESHOLD_TEMP", "35.0"))
        self.moisture_threshold = float(os.getenv("ANOMALY_THRESHOLD_MOISTURE", "30.0"))
        self.ph_threshold_high = float(os.getenv("ANOMALY_THRESHOLD_PH", "8.5"))
        self.ph_threshold_low = 5.5
    
    def detect_anomalies(self, db: Session, field_id: str = None) -> List[Dict[str, Any]]:
        """
        Detect anomalies across all fields or specific field
        Returns list of detected anomalies
        """
        anomalies = []
        
        # Get latest sensor data
        query = db.query(SensorData)
        if field_id:
            query = query.filter(SensorData.field_id == field_id)
        
        # Only check recent data (last 5 minutes)
        recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
        recent_data = query.filter(SensorData.timestamp >= recent_cutoff).all()
        
        for sensor_reading in recent_data:
            # Check for temperature anomalies
            if sensor_reading.temperature > self.temp_threshold:
                anomalies.append({
                    "field_id": sensor_reading.field_id,
                    "type": "temperature_spike",
                    "severity": "high" if sensor_reading.temperature > 40 else "medium",
                    "value": sensor_reading.temperature,
                    "threshold": self.temp_threshold,
                    "message": f"Temperature spike detected: {sensor_reading.temperature}°C (threshold: {self.temp_threshold}°C)",
                    "timestamp": sensor_reading.timestamp
                })
            
            # Check for low moisture
            if sensor_reading.soil_moisture < self.moisture_threshold:
                severity = "critical" if sensor_reading.soil_moisture < 20 else "high"
                anomalies.append({
                    "field_id": sensor_reading.field_id,
                    "type": "low_moisture",
                    "severity": severity,
                    "value": sensor_reading.soil_moisture,
                    "threshold": self.moisture_threshold,
                    "message": f"Critical soil moisture level: {sensor_reading.soil_moisture}% (threshold: {self.moisture_threshold}%)",
                    "timestamp": sensor_reading.timestamp
                })
            
            # Check for pH imbalance
            if sensor_reading.ph_level > self.ph_threshold_high or sensor_reading.ph_level < self.ph_threshold_low:
                anomalies.append({
                    "field_id": sensor_reading.field_id,
                    "type": "ph_imbalance",
                    "severity": "medium",
                    "value": sensor_reading.ph_level,
                    "threshold": f"{self.ph_threshold_low}-{self.ph_threshold_high}",
                    "message": f"pH imbalance detected: {sensor_reading.ph_level} (ideal: {self.ph_threshold_low}-{self.ph_threshold_high})",
                    "timestamp": sensor_reading.timestamp
                })
            
            # Check for extreme nutrient levels
            if sensor_reading.nitrogen < 30:
                anomalies.append({
                    "field_id": sensor_reading.field_id,
                    "type": "nitrogen_deficiency",
                    "severity": "medium",
                    "value": sensor_reading.nitrogen,
                    "threshold": 30,
                    "message": f"Nitrogen deficiency: {sensor_reading.nitrogen} ppm (minimum: 30 ppm)",
                    "timestamp": sensor_reading.timestamp
                })
            
            # Detect rapid changes (compare with data from 1 hour ago)
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            previous_data = db.query(SensorData).filter(
                SensorData.field_id == sensor_reading.field_id,
                SensorData.timestamp >= hour_ago,
                SensorData.timestamp < sensor_reading.timestamp
            ).order_by(SensorData.timestamp.desc()).first()
            
            if previous_data:
                # Check for rapid temperature change
                temp_change = abs(sensor_reading.temperature - previous_data.temperature)
                if temp_change > 8:  # More than 8°C change in 1 hour
                    anomalies.append({
                        "field_id": sensor_reading.field_id,
                        "type": "rapid_temperature_change",
                        "severity": "medium",
                        "value": temp_change,
                        "threshold": 8,
                        "message": f"Rapid temperature change: {temp_change}°C in 1 hour",
                        "timestamp": sensor_reading.timestamp
                    })
                
                # Check for rapid moisture drop
                moisture_change = previous_data.soil_moisture - sensor_reading.soil_moisture
                if moisture_change > 15:  # More than 15% drop in 1 hour
                    anomalies.append({
                        "field_id": sensor_reading.field_id,
                        "type": "rapid_moisture_drop",
                        "severity": "high",
                        "value": moisture_change,
                        "threshold": 15,
                        "message": f"Rapid moisture drop: {moisture_change}% in 1 hour (possible irrigation failure)",
                        "timestamp": sensor_reading.timestamp
                    })
        
        return anomalies
    
    def create_alerts(self, db: Session, anomalies: List[Dict[str, Any]]) -> List[Alert]:
        """
        Create alert records for detected anomalies
        """
        created_alerts = []
        
        for anomaly in anomalies:
            # Check if similar alert already exists and is unresolved
            existing_alert = db.query(Alert).filter(
                Alert.field_id == anomaly["field_id"],
                Alert.alert_type == anomaly["type"],
                Alert.is_resolved == False,
                Alert.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    field_id=anomaly["field_id"],
                    severity=anomaly["severity"],
                    alert_type=anomaly["type"],
                    message=anomaly["message"],
                    is_resolved=False,
                    auto_remediation_applied=False
                )
                db.add(alert)
                created_alerts.append(alert)
        
        db.commit()
        return created_alerts
    
    def monitor_and_alert(self, db: Session, field_id: str = None) -> Dict[str, Any]:
        """
        Complete monitoring cycle: detect anomalies and create alerts
        """
        anomalies = self.detect_anomalies(db, field_id)
        created_alerts = self.create_alerts(db, anomalies)
        
        return {
            "anomalies_detected": len(anomalies),
            "alerts_created": len(created_alerts),
            "anomalies": anomalies,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_trend_analysis(self, db: Session, field_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze trends over time for predictive insights
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        history = db.query(SensorData).filter(
            SensorData.field_id == field_id,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp).all()
        
        if len(history) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        # Calculate trends
        temperatures = [h.temperature for h in history]
        moistures = [h.soil_moisture for h in history]
        
        # Simple linear trend (increasing/decreasing/stable)
        temp_trend = "stable"
        if temperatures[-1] > temperatures[0] + 3:
            temp_trend = "increasing"
        elif temperatures[-1] < temperatures[0] - 3:
            temp_trend = "decreasing"
        
        moisture_trend = "stable"
        if moistures[-1] > moistures[0] + 5:
            moisture_trend = "increasing"
        elif moistures[-1] < moistures[0] - 5:
            moisture_trend = "decreasing"
        
        # Predict issues
        predictions = []
        
        # If moisture is decreasing and already below 40%, predict irrigation need
        if moisture_trend == "decreasing" and moistures[-1] < 40:
            hours_until_critical = ((moistures[-1] - 25) / ((moistures[0] - moistures[-1]) / hours)) if moistures[0] != moistures[-1] else 0
            predictions.append({
                "type": "irrigation_needed",
                "estimated_time_hours": max(0, hours_until_critical),
                "confidence": "high" if moisture_trend == "decreasing" else "medium"
            })
        
        # If temperature is increasing and above 30°C, predict heat stress
        if temp_trend == "increasing" and temperatures[-1] > 30:
            predictions.append({
                "type": "heat_stress_risk",
                "estimated_time_hours": 2,
                "confidence": "medium"
            })
        
        return {
            "field_id": field_id,
            "period_hours": hours,
            "temperature_trend": temp_trend,
            "moisture_trend": moisture_trend,
            "current_temp": temperatures[-1],
            "current_moisture": moistures[-1],
            "predictions": predictions,
            "data_points_analyzed": len(history)
        }
