# 🧪 Testing Guide - Smart Farm AIOps Platform

## Quick Test Scenarios

### Scenario 1: Complete End-to-End Workflow

**Objective:** Test the full multi-agent + AIOps pipeline

1. **Start the system:**
   ```bash
   # Terminal 1
   python app/main.py
   
   # Terminal 2
   python ui/dashboard.py
   ```

2. **Generate test data with anomalies:**
   ```bash
   python data/seed_data.py
   ```
   - This creates field_A1 with low moisture (<25%)
   - field_B1 with temperature spike (>38°C)
   - field_C1 with nitrogen deficiency (<25 ppm)

3. **Trigger AIOps monitoring:**
   - Open dashboard at http://localhost:7860
   - Go to "AIOps" tab
   - Click "Run AIOps Monitor"
   - **Expected:** 3+ anomalies detected, alerts created, auto-remediation executed

4. **Query the AI agent:**
   - Go to "AI Agent" tab
   - Query: "Which fields need immediate attention?"
   - **Expected:** Agent identifies all 3 problem fields with specific recommendations

5. **Verify auto-remediation:**
   - Check "Active Alerts" section
   - **Expected:** Alerts show "Auto-remediation: ✅ Applied"
   - Check cost estimates for each action

---

### Scenario 2: Natural Language Diagnostics

**Test various query types:**

| Query | Expected Agent Behavior |
|-------|------------------------|
| "Show me soil health for field_A1" | Calls `analyze_soil_health()`, returns NPK status |
| "Which fields need irrigation?" | Calls `check_irrigation_efficiency()` for all fields |
| "What's causing low moisture in field_B1?" | Multi-tool call: gets history + checks irrigation |
| "Predict issues for the next 6 hours" | Calls `get_field_history()` + trend analysis |

**How to test:**
```bash
curl -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me soil health for field_A1",
    "field_id": "field_A1"
  }'
```

---

### Scenario 3: AIOps Anomaly Detection

**Test different anomaly types:**

1. **Temperature Spike:**
   ```python
   # Add this to seed_data.py or submit via API
   POST /api/sensors/data
   {
     "field_id": "field_TEST",
     "temperature": 42.0,  # Above threshold (35°C)
     "soil_moisture": 60.0,
     "ph_level": 6.8,
     "nitrogen": 80,
     "phosphorus": 35,
     "potassium": 70,
     "humidity": 65
   }
   ```
   **Expected:** Alert created with severity "high", cooling system recommended

2. **Critical Moisture Drop:**
   ```python
   POST /api/sensors/data
   {
     "field_id": "field_TEST",
     "temperature": 28.0,
     "soil_moisture": 18.0,  # Below critical (20%)
     "ph_level": 6.8,
     ...
   }
   ```
   **Expected:** Alert severity "critical", irrigation auto-triggered

3. **pH Imbalance:**
   ```python
   POST /api/sensors/data
   {
     "field_id": "field_TEST",
     "temperature": 28.0,
     "soil_moisture": 55.0,
     "ph_level": 9.2,  # Above threshold (8.5)
     ...
   }
   ```
   **Expected:** Alert created, farmer notification sent

---

### Scenario 4: Cost Tracking Validation

**Verify cost calculations:**

1. Trigger irrigation for field_A1
2. Check remediation history:
   ```bash
   GET /api/remediation/history?field_id=field_A1
   ```
3. **Expected costs:**
   - Irrigation (300L): ₹15.00
   - Fertilizer (25kg nitrogen): ₹1,125.00
   - Cooling (2hr misting): ₹30.00
   - SMS alert: ₹0.50

4. Verify 24-hour totals in dashboard stats

---

### Scenario 5: Multi-Agent Coordination

**Test orchestrator logic:**

1. **Query:** "Field A1 has low moisture and nitrogen deficiency. What should I do?"

2. **Expected workflow:**
   ```
   Orchestrator
   ├─> Diagnostic Agent
   │   ├─> get_latest_sensor_data(field_A1)
   │   ├─> analyze_soil_health(field_A1)
   │   └─> check_irrigation_efficiency(field_A1)
   │
   └─> Action Agent (if issues found)
       ├─> trigger_irrigation(300L)
       ├─> apply_fertilizer(nitrogen, 25kg)
       └─> send_farmer_alert()
   ```

3. **Validation:**
   - Check `agent_logs` table for both agents
   - Verify `remediation_logs` table has 2-3 actions
   - Confirm alerts updated with remediation status

---

## Performance Benchmarks

### Expected Response Times

| Operation | Target Time | Notes |
|-----------|-------------|-------|
| Simple query (1 tool call) | <3s | e.g., "Latest data for field_A1" |
| Complex query (3-5 tools) | <8s | e.g., "Comprehensive health check" |
| AIOps monitoring (all fields) | <5s | Anomaly detection + alerting |
| Auto-remediation | <2s | Per action executed |
| Trend analysis | <1s | Historical data processing |

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test sensor data endpoint
ab -n 100 -c 10 http://localhost:8000/api/sensors/latest/field_A1

# Test agent query (POST)
ab -n 50 -c 5 -p query.json -T application/json \
   http://localhost:8000/api/agent/query
```

**Target:** 50+ req/s for GET endpoints, 10+ req/s for AI agent queries

---

## Database Validation

### Check data integrity:

```bash
# Connect to SQLite
sqlite3 smart_farm.db

# Verify sensor data
SELECT field_id, COUNT(*) as readings, 
       MIN(timestamp) as earliest, 
       MAX(timestamp) as latest
FROM sensor_data
GROUP BY field_id;

# Check alerts
SELECT field_id, severity, COUNT(*) as count
FROM alerts
WHERE is_resolved = 0
GROUP BY field_id, severity;

# Remediation costs
SELECT action_type, COUNT(*) as actions, 
       SUM(cost_estimate) as total_cost
FROM remediation_logs
GROUP BY action_type;
```

---

## Troubleshooting Common Issues

### Issue 1: "OpenRouter API Error"

**Symptoms:** Agent queries fail with 401/403 errors

**Fix:**
```bash
# Check .env file
cat .env | grep OPENROUTER_API_KEY

# Test API key manually
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Issue 2: "No anomalies detected"

**Symptoms:** AIOps monitor returns 0 anomalies even with bad data

**Fix:**
- Verify thresholds in `.env`:
  ```
  ANOMALY_THRESHOLD_TEMP=35.0
  ANOMALY_THRESHOLD_MOISTURE=30.0
  ```
- Check sensor data timestamps (must be <5 min old)
- Manually trigger with recent data:
  ```bash
  # Add new reading
  POST /api/sensors/data {...}
  
  # Immediately monitor
  POST /api/aiops/monitor
  ```

### Issue 3: "Auto-remediation not executing"

**Symptoms:** Alerts created but no actions in remediation_logs

**Fix:**
- Check `.env`: `AUTO_REMEDIATION_ENABLED=true`
- Verify alert severity meets threshold
- Check alert type has remediation rule in `auto_remediation.py`

### Issue 4: "Dashboard shows connection error"

**Symptoms:** Gradio UI can't reach API

**Fix:**
```bash
# Verify API is running
curl http://localhost:8000/health

# Check firewall
sudo ufw allow 8000
sudo ufw allow 7860

# Update dashboard API_BASE_URL in ui/dashboard.py
```

---

## Automated Test Suite

Create `tests/test_all.py`:

```python
import pytest
import requests

API_BASE = "http://localhost:8000"

def test_health():
    r = requests.get(f"{API_BASE}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

def test_sensor_data_submission():
    data = {
        "field_id": "test_field",
        "temperature": 28.5,
        "soil_moisture": 55.0,
        "ph_level": 6.8,
        "nitrogen": 80,
        "phosphorus": 35,
        "potassium": 70,
        "humidity": 65
    }
    r = requests.post(f"{API_BASE}/api/sensors/data", json=data)
    assert r.status_code == 200

def test_agent_query():
    query = {
        "query": "What is the current temperature?",
        "field_id": "field_A1"
    }
    r = requests.post(f"{API_BASE}/api/agent/query", json=query)
    assert r.status_code == 200
    result = r.json()
    assert "diagnostic_phase" in result

def test_aiops_monitor():
    r = requests.post(f"{API_BASE}/api/aiops/monitor")
    assert r.status_code == 200
    assert "anomalies_detected" in r.json()

# Run: pytest tests/test_all.py -v
```

---

## Demo Checklist

Before presenting the project, verify:

- [ ] API server starts without errors
- [ ] Dashboard loads and shows stats
- [ ] At least 3 fields have data (48h worth)
- [ ] Active alerts exist (from anomaly detection)
- [ ] Agent can answer queries in <5s
- [ ] AIOps monitoring detects anomalies
- [ ] Auto-remediation logs show cost estimates
- [ ] Sensor visualizations render correctly
- [ ] README examples work as documented

---

## Success Metrics

**For Resume/Interview Discussion:**

| Metric | Target Value | What It Shows |
|--------|--------------|---------------|
| Query response time | <5s avg | Efficient agentic reasoning |
| Anomaly detection accuracy | >90% | Proper threshold tuning |
| Auto-remediation rate | >70% | Autonomous operation |
| Cost tracking precision | 100% | Production-ready |
| Multi-agent coordination | 5+ tool calls | Complex reasoning |

**Example talking point:**
> "The platform processes natural language queries with 3-5 agent tool calls in under 5 seconds, achieving 90%+ accuracy in anomaly detection and autonomously remediating 70% of alerts without human intervention."
