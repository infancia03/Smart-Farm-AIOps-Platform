from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - Using SQLite for easy setup (you can switch to MySQL)
DATABASE_URL = "sqlite:///./smart_farm.db"
# For MySQL: f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(String(50), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)  # Celsius
    soil_moisture = Column(Float)  # Percentage
    ph_level = Column(Float)
    nitrogen = Column(Float)  # ppm
    phosphorus = Column(Float)  # ppm
    potassium = Column(Float)  # ppm
    humidity = Column(Float)  # Percentage
    
class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(String(50), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(String(20))  # low, medium, high, critical
    alert_type = Column(String(50))  # temperature_spike, low_moisture, ph_imbalance, etc.
    message = Column(Text)
    is_resolved = Column(Boolean, default=False)
    auto_remediation_applied = Column(Boolean, default=False)
    remediation_action = Column(Text, nullable=True)
    
class RemediationLog(Base):
    __tablename__ = "remediation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, index=True)
    field_id = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    action_type = Column(String(50))  # irrigation, fertilization, cooling, etc.
    action_details = Column(Text)
    success = Column(Boolean, default=True)
    cost_estimate = Column(Float, nullable=True)  # in INR
    
class AgentLog(Base):
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent_type = Column(String(50))  # diagnostic, action, orchestrator
    query = Column(Text)
    response = Column(Text)
    tools_used = Column(Text)
    execution_time = Column(Float)  # seconds

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")
