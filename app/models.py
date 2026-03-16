from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class SensorDataCreate(BaseModel):
    field_id: str
    temperature: float = Field(..., ge=-10, le=60)
    soil_moisture: float = Field(..., ge=0, le=100)
    ph_level: float = Field(..., ge=0, le=14)
    nitrogen: float = Field(..., ge=0, le=500)
    phosphorus: float = Field(..., ge=0, le=500)
    potassium: float = Field(..., ge=0, le=500)
    humidity: float = Field(..., ge=0, le=100)

class SensorDataResponse(SensorDataCreate):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    field_id: str
    timestamp: datetime
    severity: str
    alert_type: str
    message: str
    is_resolved: bool
    auto_remediation_applied: bool
    remediation_action: Optional[str]
    
    class Config:
        from_attributes = True

class AgentQuery(BaseModel):
    query: str
    field_id: Optional[str] = None
    
class AgentResponse(BaseModel):
    response: str
    tools_used: List[str]
    execution_time: float
    recommendations: Optional[List[str]] = None

class RemediationRequest(BaseModel):
    alert_id: int
    action_type: str
    manual_override: bool = False
