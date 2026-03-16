#!/usr/bin/env python3
"""
Quick Demo Script - Smart Farm AIOps Platform
Runs automated tests to showcase the system
"""

import requests
import time
import json

API_BASE = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_api_health():
    print_section("1. Testing API Health")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_dashboard_stats():
    print_section("2. Dashboard Statistics")
    response = requests.get(f"{API_BASE}/api/dashboard/stats")
    print(json.dumps(response.json(), indent=2))

def test_sensor_data():
    print_section("3. Latest Sensor Data - Field A1")
    response = requests.get(f"{API_BASE}/api/sensors/latest/field_A1")
    data = response.json()
    print(f"Temperature: {data['temperature']}°C")
    print(f"Soil Moisture: {data['soil_moisture']}%")
    print(f"pH Level: {data['ph_level']}")
    print(f"Nitrogen: {data['nitrogen']} ppm")
    print(f"Phosphorus: {data['phosphorus']} ppm")
    print(f"Potassium: {data['potassium']} ppm")

def test_agentic_query():
    print_section("4. Agentic AI Query")
    
    query = {
        "query": "Analyze the current health status of field_A1 and recommend any necessary actions",
        "field_id": "field_A1"
    }
    
    print(f"Query: {query['query']}")
    print("\nCalling diagnostic and action agents...")
    
    response = requests.post(f"{API_BASE}/api/agent/query", json=query)
    result = response.json()
    
    print("\n--- Orchestrator Summary ---")
    print(result.get('orchestrator_summary', 'N/A')[:300] + "...")
    
    if 'action_phase' in result and 'actions_taken' in result['action_phase']:
        print(f"\n✓ Actions Executed: {result['action_phase']['total_actions']}")
        print(f"✓ Total Cost: ₹{result['action_phase']['total_cost_inr']}")

def test_aiops_monitoring():
    print_section("5. AIOps Anomaly Detection")
    
    print("Running anomaly detection...")
    response = requests.post(f"{API_BASE}/api/aiops/monitor")
    result = response.json()
    
    print(f"\n✓ Anomalies Detected: {result['anomalies_detected']}")
    print(f"✓ Alerts Created: {result['alerts_created']}")
    
    if 'auto_remediation' in result:
        remediation = result['auto_remediation']
        print(f"\n--- Auto-Remediation ---")
        print(f"✓ Actions Executed: {remediation['remediations_executed']}")
        print(f"✓ Total Cost: ₹{remediation['total_cost_inr']}")

def test_active_alerts():
    print_section("6. Active Alerts")
    
    response = requests.get(f"{API_BASE}/api/alerts?resolved=false")
    alerts = response.json()
    
    print(f"Total Active Alerts: {len(alerts)}\n")
    
    for i, alert in enumerate(alerts[:3], 1):
        print(f"{i}. {alert['field_id']} - {alert['alert_type']}")
        print(f"   Severity: {alert['severity']}")
        print(f"   Message: {alert['message']}")
        print(f"   Auto-remediation: {'✓ Applied' if alert['auto_remediation_applied'] else '✗ Not applied'}")
        print()

def test_trend_analysis():
    print_section("7. Predictive Trend Analysis")
    
    response = requests.get(f"{API_BASE}/api/aiops/trends/field_A1")
    result = response.json()
    
    print(f"Field: field_A1")
    print(f"Temperature Trend: {result['temperature_trend']} (Current: {result['current_temp']}°C)")
    print(f"Moisture Trend: {result['moisture_trend']} (Current: {result['current_moisture']}%)")
    
    if result['predictions']:
        print("\n🔮 Predictions:")
        for pred in result['predictions']:
            print(f"  - {pred['type']} in ~{pred['estimated_time_hours']:.1f}h (Confidence: {pred['confidence']})")

def main():
    print("\n")
    print("🌾 SMART FARM AIOPS PLATFORM - AUTOMATED DEMO")
    print("=" * 60)
    print("\nThis demo will showcase all major features of the platform.")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("\nPress Ctrl+C to stop at any time.\n")
    
    input("Press Enter to start the demo...")
    
    try:
        test_api_health()
        time.sleep(1)
        
        test_dashboard_stats()
        time.sleep(1)
        
        test_sensor_data()
        time.sleep(1)
        
        test_agentic_query()
        time.sleep(2)
        
        test_aiops_monitoring()
        time.sleep(1)
        
        test_active_alerts()
        time.sleep(1)
        
        test_trend_analysis()
        
        print_section("✅ Demo Complete!")
        print("All features demonstrated successfully!")
        print("\nNext steps:")
        print("  1. Open Gradio dashboard: python ui/dashboard.py")
        print("  2. Visit http://localhost:7860")
        print("  3. Try natural language queries in the AI Agent tab")
        print("  4. Explore sensor visualizations and AIOps monitoring")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("Please start the server first: python app/main.py")
    except KeyboardInterrupt:
        print("\n\nDemo stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
