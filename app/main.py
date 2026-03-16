from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from app.database import get_db, init_db, SensorData, Alert
from app.models import (
    SensorDataCreate, SensorDataResponse, AlertResponse, 
    AgentQuery, AgentResponse, RemediationRequest
)
from app.agents.orchestrator import OrchestratorAgent
from app.aiops.anomaly_detector import AnomalyDetector
from app.aiops.auto_remediation import AutoRemediationEngine
from datetime import datetime, timedelta

# Initialize FastAPI app
app = FastAPI(
    title="Smart Farm AIOps Platform",
    description="AI-powered agricultural monitoring and auto-remediation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator = OrchestratorAgent()
anomaly_detector = AnomalyDetector()
auto_remediation = AutoRemediationEngine()

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    print("✅ Smart Farm AIOps Platform started successfully!")

# ============= SENSOR DATA ENDPOINTS =============

@app.post("/api/sensors/data", response_model=SensorDataResponse, tags=["Sensors"])
def create_sensor_data(data: SensorDataCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Submit new sensor data and trigger automatic anomaly detection
    """
    # Create sensor data record
    db_sensor = SensorData(**data.dict())
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    
    # Trigger anomaly detection in background
    background_tasks.add_task(run_aiops_monitoring, data.field_id, db)
    
    return db_sensor

@app.get("/api/sensors/data/{field_id}", response_model=List[SensorDataResponse], tags=["Sensors"])
def get_sensor_data(field_id: str, hours: int = 24, db: Session = Depends(get_db)):
    """
    Get historical sensor data for a field
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)
    data = db.query(SensorData).filter(
        SensorData.field_id == field_id,
        SensorData.timestamp >= start_time
    ).order_by(SensorData.timestamp.desc()).all()
    
    return data

@app.get("/api/sensors/latest/{field_id}", response_model=SensorDataResponse, tags=["Sensors"])
def get_latest_sensor_data(field_id: str, db: Session = Depends(get_db)):
    """
    Get the most recent sensor reading for a field
    """
    latest = db.query(SensorData).filter(
        SensorData.field_id == field_id
    ).order_by(SensorData.timestamp.desc()).first()
    
    if not latest:
        raise HTTPException(status_code=404, detail=f"No data found for field {field_id}")
    
    return latest

# ============= AGENTIC AI ENDPOINTS =============

@app.post("/api/agent/query", tags=["Agentic AI"])
def query_agent(query: AgentQuery, db: Session = Depends(get_db)):
    """
    Query the multi-agent system for farm insights and recommendations
    
    The orchestrator will:
    1. Use diagnostic agent to analyze the situation
    2. Use action agent to plan remediation if needed
    3. Return comprehensive response
    """
    result = orchestrator.process_query(
        query=query.query,
        db=db,
        field_id=query.field_id,
        auto_remediate=True
    )
    
    return result

@app.get("/api/agent/recommendations/{field_id}", tags=["Agentic AI"])
def get_field_recommendations(field_id: str, db: Session = Depends(get_db)):
    """
    Get comprehensive AI-powered recommendations for a specific field
    """
    result = orchestrator.get_field_recommendations(field_id, db)
    return result

# ============= AIOPS MONITORING ENDPOINTS =============

@app.post("/api/aiops/monitor", tags=["AIOps"])
def monitor_anomalies(field_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Manually trigger anomaly detection and alerting
    """
    result = anomaly_detector.monitor_and_alert(db, field_id)
    
    # If anomalies detected, trigger auto-remediation
    if result["alerts_created"] > 0:
        remediation_result = auto_remediation.process_alerts(db, field_id)
        result["auto_remediation"] = remediation_result
    
    return result

@app.get("/api/aiops/trends/{field_id}", tags=["AIOps"])
def get_trend_analysis(field_id: str, hours: int = 24, db: Session = Depends(get_db)):
    """
    Get predictive trend analysis for a field
    """
    result = anomaly_detector.get_trend_analysis(db, field_id, hours)
    return result

# ============= ALERT ENDPOINTS =============

@app.get("/api/alerts", response_model=List[AlertResponse], tags=["Alerts"])
def get_alerts(
    field_id: Optional[str] = None,
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get alerts with optional filters
    """
    query = db.query(Alert)
    
    if field_id:
        query = query.filter(Alert.field_id == field_id)
    if resolved is not None:
        query = query.filter(Alert.is_resolved == resolved)
    if severity:
        query = query.filter(Alert.severity == severity)
    
    alerts = query.order_by(Alert.timestamp.desc()).limit(100).all()
    return alerts

@app.patch("/api/alerts/{alert_id}/resolve", tags=["Alerts"])
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Mark an alert as resolved
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_resolved = True
    db.commit()
    
    return {"message": "Alert resolved", "alert_id": alert_id}

# ============= REMEDIATION ENDPOINTS =============

@app.post("/api/remediation/execute", tags=["Remediation"])
def execute_manual_remediation(request: RemediationRequest, db: Session = Depends(get_db)):
    """
    Manually execute remediation action for an alert
    """
    alert = db.query(Alert).filter(Alert.id == request.alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    result = auto_remediation.execute_remediation(db, alert)
    return result

@app.get("/api/remediation/history", tags=["Remediation"])
def get_remediation_history(field_id: Optional[str] = None, hours: int = 24, db: Session = Depends(get_db)):
    """
    Get history of auto-remediation actions
    """
    result = auto_remediation.get_remediation_history(db, field_id, hours)
    return result

# ============= DASHBOARD STATS ENDPOINT =============

@app.get("/api/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive dashboard statistics
    """
    # Get all fields
    fields = db.query(SensorData.field_id).distinct().all()
    field_ids = [f[0] for f in fields]
    
    # Get active alerts
    active_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
    critical_alerts = db.query(Alert).filter(
        Alert.is_resolved == False,
        Alert.severity == "critical"
    ).count()
    
    # Get recent sensor data count
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_readings = db.query(SensorData).filter(
        SensorData.timestamp >= hour_ago
    ).count()
    
    # Get remediation stats (last 24 hours)
    remediation_stats = auto_remediation.get_remediation_history(db, hours=24)
    
    return {
        "total_fields": len(field_ids),
        "active_alerts": active_alerts,
        "critical_alerts": critical_alerts,
        "recent_readings_1h": recent_readings,
        "remediation_summary": {
            "total_actions_24h": remediation_stats["total_remediations"],
            "total_cost_24h": remediation_stats["total_cost_inr"]
        },
        "field_ids": field_ids,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============= BACKGROUND TASKS =============

def run_aiops_monitoring(field_id: str, db: Session):
    """Background task for AIOps monitoring"""
    # Detect anomalies
    result = anomaly_detector.monitor_and_alert(db, field_id)
    
    # Auto-remediate if needed
    if result["alerts_created"] > 0:
        auto_remediation.process_alerts(db, field_id)

# ============= HEALTH CHECK =============

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Smart Farm AIOps Platform",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
