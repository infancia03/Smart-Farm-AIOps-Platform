from sqlalchemy.orm import Session
from app.database import SensorData, Alert
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

class SensorTools:
    """Tools for analyzing sensor data"""
    
    @staticmethod
    def get_latest_sensor_data(db: Session, field_id: str) -> Dict[str, Any]:
        """Get the most recent sensor reading for a field"""
        latest = db.query(SensorData).filter(
            SensorData.field_id == field_id
        ).order_by(SensorData.timestamp.desc()).first()
        
        if not latest:
            return {"error": f"No data found for field {field_id}"}
        
        return {
            "field_id": latest.field_id,
            "timestamp": latest.timestamp.isoformat(),
            "temperature": latest.temperature,
            "soil_moisture": latest.soil_moisture,
            "ph_level": latest.ph_level,
            "nitrogen": latest.nitrogen,
            "phosphorus": latest.phosphorus,
            "potassium": latest.potassium,
            "humidity": latest.humidity
        }
    
    @staticmethod
    def analyze_soil_health(db: Session, field_id: str) -> Dict[str, Any]:
        """Analyze soil health based on NPK levels and pH"""
        latest = db.query(SensorData).filter(
            SensorData.field_id == field_id
        ).order_by(SensorData.timestamp.desc()).first()
        
        if not latest:
            return {"error": f"No data found for field {field_id}"}
        
        # Ideal ranges for most crops
        ideal_ranges = {
            "nitrogen": (40, 150),
            "phosphorus": (15, 60),
            "potassium": (40, 120),
            "ph_level": (6.0, 7.5)
        }
        
        health_status = {}
        recommendations = []
        
        # Check nitrogen
        if latest.nitrogen < ideal_ranges["nitrogen"][0]:
            health_status["nitrogen"] = "deficient"
            recommendations.append("Apply nitrogen-rich fertilizer (urea or ammonium sulfate)")
        elif latest.nitrogen > ideal_ranges["nitrogen"][1]:
            health_status["nitrogen"] = "excess"
            recommendations.append("Reduce nitrogen fertilization, risk of leaf burn")
        else:
            health_status["nitrogen"] = "optimal"
        
        # Check phosphorus
        if latest.phosphorus < ideal_ranges["phosphorus"][0]:
            health_status["phosphorus"] = "deficient"
            recommendations.append("Apply phosphorus fertilizer (DAP or SSP)")
        elif latest.phosphorus > ideal_ranges["phosphorus"][1]:
            health_status["phosphorus"] = "excess"
            recommendations.append("Reduce phosphorus application")
        else:
            health_status["phosphorus"] = "optimal"
        
        # Check potassium
        if latest.potassium < ideal_ranges["potassium"][0]:
            health_status["potassium"] = "deficient"
            recommendations.append("Apply potassium fertilizer (MOP or SOP)")
        elif latest.potassium > ideal_ranges["potassium"][1]:
            health_status["potassium"] = "excess"
            recommendations.append("Reduce potassium application")
        else:
            health_status["potassium"] = "optimal"
        
        # Check pH
        if latest.ph_level < ideal_ranges["ph_level"][0]:
            health_status["ph"] = "acidic"
            recommendations.append("Apply lime to increase pH")
        elif latest.ph_level > ideal_ranges["ph_level"][1]:
            health_status["ph"] = "alkaline"
            recommendations.append("Apply sulfur or organic matter to decrease pH")
        else:
            health_status["ph"] = "optimal"
        
        overall_health = "healthy" if all(v == "optimal" for v in health_status.values()) else "needs_attention"
        
        return {
            "field_id": field_id,
            "overall_health": overall_health,
            "nutrient_status": health_status,
            "current_values": {
                "nitrogen": latest.nitrogen,
                "phosphorus": latest.phosphorus,
                "potassium": latest.potassium,
                "ph_level": latest.ph_level
            },
            "recommendations": recommendations
        }
    
    @staticmethod
    def check_irrigation_efficiency(db: Session, field_id: str) -> Dict[str, Any]:
        """Check if irrigation is needed based on moisture levels"""
        latest = db.query(SensorData).filter(
            SensorData.field_id == field_id
        ).order_by(SensorData.timestamp.desc()).first()
        
        if not latest:
            return {"error": f"No data found for field {field_id}"}
        
        # Get historical data for last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        historical = db.query(SensorData).filter(
            SensorData.field_id == field_id,
            SensorData.timestamp >= yesterday
        ).all()
        
        moisture_trend = "stable"
        if len(historical) > 2:
            recent_moisture = [h.soil_moisture for h in historical[-5:]]
            if all(recent_moisture[i] > recent_moisture[i+1] for i in range(len(recent_moisture)-1)):
                moisture_trend = "decreasing"
            elif all(recent_moisture[i] < recent_moisture[i+1] for i in range(len(recent_moisture)-1)):
                moisture_trend = "increasing"
        
        # Irrigation recommendations
        irrigation_needed = False
        urgency = "none"
        estimated_water = 0
        
        if latest.soil_moisture < 30:
            irrigation_needed = True
            urgency = "critical"
            estimated_water = 500  # liters per hectare
        elif latest.soil_moisture < 45:
            irrigation_needed = True
            urgency = "moderate"
            estimated_water = 300
        elif latest.soil_moisture < 60 and moisture_trend == "decreasing":
            irrigation_needed = True
            urgency = "low"
            estimated_water = 200
        
        return {
            "field_id": field_id,
            "current_moisture": latest.soil_moisture,
            "moisture_trend": moisture_trend,
            "irrigation_needed": irrigation_needed,
            "urgency": urgency,
            "estimated_water_needed_liters": estimated_water,
            "estimated_cost_inr": estimated_water * 0.05  # ₹0.05 per liter
        }
    
    @staticmethod
    def detect_pest_patterns(db: Session, field_id: str) -> Dict[str, Any]:
        """Detect potential pest issues based on environmental conditions"""
        latest = db.query(SensorData).filter(
            SensorData.field_id == field_id
        ).order_by(SensorData.timestamp.desc()).first()
        
        if not latest:
            return {"error": f"No data found for field {field_id}"}
        
        pest_risks = []
        
        # High temperature + high humidity = fungal diseases
        if latest.temperature > 30 and latest.humidity > 75:
            pest_risks.append({
                "type": "fungal_disease",
                "risk_level": "high",
                "conditions": "High temperature and humidity favor fungal growth",
                "recommendation": "Apply fungicide preventively, improve air circulation"
            })
        
        # Low moisture + high temperature = spider mites
        if latest.soil_moisture < 40 and latest.temperature > 32:
            pest_risks.append({
                "type": "spider_mites",
                "risk_level": "moderate",
                "conditions": "Hot and dry conditions favor spider mites",
                "recommendation": "Increase irrigation, monitor leaf undersides"
            })
        
        # High nitrogen = aphid attraction
        if latest.nitrogen > 150:
            pest_risks.append({
                "type": "aphids",
                "risk_level": "moderate",
                "conditions": "Excess nitrogen causes lush growth that attracts aphids",
                "recommendation": "Reduce nitrogen fertilization, introduce beneficial insects"
            })
        
        risk_level = "high" if any(r["risk_level"] == "high" for r in pest_risks) else \
                     "moderate" if pest_risks else "low"
        
        return {
            "field_id": field_id,
            "overall_pest_risk": risk_level,
            "detected_risks": pest_risks,
            "environmental_conditions": {
                "temperature": latest.temperature,
                "humidity": latest.humidity,
                "soil_moisture": latest.soil_moisture,
                "nitrogen": latest.nitrogen
            }
        }
    
    @staticmethod
    def get_field_history(db: Session, field_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get historical sensor data for a field"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        history = db.query(SensorData).filter(
            SensorData.field_id == field_id,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp).all()
        
        if not history:
            return {"error": f"No historical data found for field {field_id}"}
        
        # Calculate statistics
        temps = [h.temperature for h in history]
        moistures = [h.soil_moisture for h in history]
        
        return {
            "field_id": field_id,
            "period_hours": hours,
            "data_points": len(history),
            "temperature_stats": {
                "min": min(temps),
                "max": max(temps),
                "avg": statistics.mean(temps),
                "current": temps[-1]
            },
            "moisture_stats": {
                "min": min(moistures),
                "max": max(moistures),
                "avg": statistics.mean(moistures),
                "current": moistures[-1]
            }
        }
    
    @staticmethod
    def get_active_alerts(db: Session, field_id: str = None) -> Dict[str, Any]:
        """Get active (unresolved) alerts"""
        query = db.query(Alert).filter(Alert.is_resolved == False)
        
        if field_id:
            query = query.filter(Alert.field_id == field_id)
        
        alerts = query.order_by(Alert.timestamp.desc()).all()
        
        return {
            "total_active_alerts": len(alerts),
            "alerts": [
                {
                    "id": a.id,
                    "field_id": a.field_id,
                    "severity": a.severity,
                    "type": a.alert_type,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat(),
                    "auto_remediation_applied": a.auto_remediation_applied
                }
                for a in alerts
            ]
        }
