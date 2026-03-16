from sqlalchemy.orm import Session
from app.database import Alert, RemediationLog
from app.agents.action_agent import ActionAgent
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class AutoRemediationEngine:
    """
    AIOps Auto-Remediation Engine
    Automatically executes remediation actions for detected anomalies
    """
    
    def __init__(self):
        self.action_agent = ActionAgent()
        self.enabled = os.getenv("AUTO_REMEDIATION_ENABLED", "true").lower() == "true"
        
        # Define auto-remediation rules
        self.remediation_rules = {
            "low_moisture": {
                "action": "trigger_irrigation",
                "severity_threshold": "high",
                "parameters": {
                    "water_amount_liters": 300,
                    "duration_minutes": 45
                }
            },
            "temperature_spike": {
                "action": "activate_cooling_system",
                "severity_threshold": "high",
                "parameters": {
                    "cooling_method": "misting",
                    "duration_hours": 2
                }
            },
            "nitrogen_deficiency": {
                "action": "apply_fertilizer",
                "severity_threshold": "medium",
                "parameters": {
                    "fertilizer_type": "nitrogen",
                    "amount_kg": 25
                }
            },
            "ph_imbalance": {
                "action": "send_farmer_alert",
                "severity_threshold": "medium",
                "parameters": {
                    "message": "pH imbalance detected. Manual soil amendment recommended.",
                    "urgency": "medium"
                }
            },
            "rapid_moisture_drop": {
                "action": "send_farmer_alert",
                "severity_threshold": "high",
                "parameters": {
                    "message": "Rapid moisture drop detected. Possible irrigation system failure.",
                    "urgency": "critical"
                }
            }
        }
    
    def should_remediate(self, alert: Alert) -> bool:
        """
        Determine if an alert should trigger auto-remediation
        """
        if not self.enabled:
            return False
        
        # Check if alert type has a remediation rule
        if alert.alert_type not in self.remediation_rules:
            return False
        
        rule = self.remediation_rules[alert.alert_type]
        
        # Check severity threshold
        severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        alert_severity = severity_levels.get(alert.severity, 0)
        required_severity = severity_levels.get(rule["severity_threshold"], 0)
        
        return alert_severity >= required_severity
    
    def execute_remediation(self, db: Session, alert: Alert) -> Dict[str, Any]:
        """
        Execute auto-remediation for an alert
        """
        if not self.should_remediate(alert):
            return {
                "executed": False,
                "reason": "Alert does not meet auto-remediation criteria"
            }
        
        rule = self.remediation_rules[alert.alert_type]
        action_type = rule["action"]
        parameters = rule["parameters"].copy()
        parameters["field_id"] = alert.field_id
        parameters["alert_id"] = alert.id
        
        # Execute the action
        result = self.action_agent.execute_action(action_type, parameters, db)
        
        # Update alert with remediation status
        alert.auto_remediation_applied = True
        alert.remediation_action = f"{action_type}: {result.get('action', 'N/A')}"
        db.commit()
        
        return {
            "executed": True,
            "alert_id": alert.id,
            "action_type": action_type,
            "result": result,
            "cost_inr": result.get("cost", 0)
        }
    
    def process_alerts(self, db: Session, field_id: str = None) -> Dict[str, Any]:
        """
        Process all unresolved alerts and execute auto-remediation
        """
        # Get unresolved alerts without auto-remediation
        query = db.query(Alert).filter(
            Alert.is_resolved == False,
            Alert.auto_remediation_applied == False
        )
        
        if field_id:
            query = query.filter(Alert.field_id == field_id)
        
        alerts = query.all()
        
        remediation_results = []
        total_cost = 0
        
        for alert in alerts:
            result = self.execute_remediation(db, alert)
            if result["executed"]:
                remediation_results.append(result)
                total_cost += result.get("cost_inr", 0)
        
        return {
            "total_alerts_processed": len(alerts),
            "remediations_executed": len(remediation_results),
            "total_cost_inr": round(total_cost, 2),
            "results": remediation_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_remediation_history(self, db: Session, field_id: str = None, hours: int = 24) -> Dict[str, Any]:
        """
        Get history of auto-remediation actions
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(RemediationLog).filter(
            RemediationLog.timestamp >= start_time
        )
        
        if field_id:
            query = query.filter(RemediationLog.field_id == field_id)
        
        logs = query.order_by(RemediationLog.timestamp.desc()).all()
        
        total_cost = sum(log.cost_estimate or 0 for log in logs)
        
        # Group by action type
        action_counts = {}
        for log in logs:
            action_counts[log.action_type] = action_counts.get(log.action_type, 0) + 1
        
        return {
            "total_remediations": len(logs),
            "total_cost_inr": round(total_cost, 2),
            "action_breakdown": action_counts,
            "recent_actions": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "field_id": log.field_id,
                    "action_type": log.action_type,
                    "success": log.success,
                    "cost_inr": log.cost_estimate
                }
                for log in logs[:10]  # Last 10 actions
            ]
        }
