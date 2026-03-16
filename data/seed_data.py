import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db, SensorData
from datetime import datetime, timedelta
import random
import numpy as np

def generate_sensor_data():
    """
    Generate realistic farm sensor data for 5 fields over 48 hours
    Includes normal patterns and some anomalies for testing
    """
    
    init_db()
    db = SessionLocal()
    
    fields = ["field_A1", "field_A2", "field_B1", "field_B2", "field_C1"]
    
    print("🌱 Generating farm sensor data...")
    
    # Generate data for last 48 hours, one reading every 15 minutes
    hours_back = 48
    interval_minutes = 15
    readings_per_field = (hours_back * 60) // interval_minutes
    
    for field_id in fields:
        print(f"  📊 Generating data for {field_id}...")
        
        # Base values for this field (with some variation)
        base_temp = random.uniform(25, 30)
        base_moisture = random.uniform(50, 70)
        base_ph = random.uniform(6.5, 7.2)
        base_nitrogen = random.uniform(60, 120)
        base_phosphorus = random.uniform(25, 50)
        base_potassium = random.uniform(60, 100)
        base_humidity = random.uniform(60, 80)
        
        for i in range(readings_per_field):
            # Calculate timestamp
            timestamp = datetime.utcnow() - timedelta(minutes=interval_minutes * (readings_per_field - i - 1))
            
            # Add time-based patterns (temperature cycles with day/night)
            hour_of_day = timestamp.hour
            
            # Temperature varies with time of day
            temp_variation = 5 * np.sin((hour_of_day - 6) * np.pi / 12)  # Peak at 2 PM
            temperature = base_temp + temp_variation + random.uniform(-1, 1)
            
            # Moisture decreases over time with some random variation
            moisture_decay = (i / readings_per_field) * 20  # Gradual decrease
            soil_moisture = max(20, base_moisture - moisture_decay + random.uniform(-3, 3))
            
            # pH is relatively stable
            ph_level = base_ph + random.uniform(-0.2, 0.2)
            
            # Nutrients decrease slightly over time (uptake)
            nutrient_decay = (i / readings_per_field) * 15
            nitrogen = max(30, base_nitrogen - nutrient_decay + random.uniform(-5, 5))
            phosphorus = max(15, base_phosphorus - nutrient_decay * 0.4 + random.uniform(-2, 2))
            potassium = max(40, base_potassium - nutrient_decay * 0.5 + random.uniform(-3, 3))
            
            # Humidity inversely correlates with temperature
            humidity = base_humidity - temp_variation * 0.5 + random.uniform(-2, 2)
            
            # Inject some anomalies in recent data (last 6 hours) for certain fields
            if i > readings_per_field - 24:  # Last 6 hours
                if field_id == "field_A1":
                    # Low moisture anomaly
                    soil_moisture = min(soil_moisture, 25)
                elif field_id == "field_B1":
                    # Temperature spike
                    temperature = max(temperature, 38)
                elif field_id == "field_C1":
                    # Nitrogen deficiency
                    nitrogen = min(nitrogen, 25)
            
            # Create sensor data record
            sensor_data = SensorData(
                field_id=field_id,
                timestamp=timestamp,
                temperature=round(temperature, 2),
                soil_moisture=round(max(0, min(100, soil_moisture)), 2),
                ph_level=round(max(0, min(14, ph_level)), 2),
                nitrogen=round(max(0, nitrogen), 2),
                phosphorus=round(max(0, phosphorus), 2),
                potassium=round(max(0, potassium), 2),
                humidity=round(max(0, min(100, humidity)), 2)
            )
            
            db.add(sensor_data)
        
        db.commit()
        print(f"  ✅ {readings_per_field} readings created for {field_id}")
    
    print(f"\n✅ Successfully generated sensor data for {len(fields)} fields!")
    print(f"📈 Total records created: {len(fields) * readings_per_field}")
    
    # Print summary of latest data
    print("\n📊 Latest sensor readings:")
    for field_id in fields:
        latest = db.query(SensorData).filter(
            SensorData.field_id == field_id
        ).order_by(SensorData.timestamp.desc()).first()
        
        print(f"\n  {field_id}:")
        print(f"    🌡️  Temperature: {latest.temperature}°C")
        print(f"    💧 Soil Moisture: {latest.soil_moisture}%")
        print(f"    🧪 pH Level: {latest.ph_level}")
        print(f"    🌾 NPK: N={latest.nitrogen}, P={latest.phosphorus}, K={latest.potassium}")
    
    db.close()

if __name__ == "__main__":
    generate_sensor_data()
