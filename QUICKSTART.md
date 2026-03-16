# 🚀 QUICK START - Smart Farm AIOps Platform

## ⚡ Get Running in 5 Minutes

### Prerequisites
- Python 3.9+ installed
- OpenRouter API key (get free at https://openrouter.ai/keys)

### Step 1: Setup (2 minutes)
```bash
cd smart-farm-aiops

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your OPENROUTER_API_KEY
```

### Step 2: Generate Data (1 minute)
```bash
python data/seed_data.py
```
This creates 48 hours of sensor data for 5 fields with realistic patterns + anomalies.

### Step 3: Start API Server (30 seconds)
```bash
# Terminal 1
python app/main.py
```
Server runs on http://localhost:8000
- API docs: http://localhost:8000/docs

### Step 4: Launch Dashboard (30 seconds)
```bash
# Terminal 2 (new terminal)
python ui/dashboard.py
```
Dashboard runs on http://localhost:7860

### Step 5: Test the System (1 minute)
```bash
# Terminal 3 (new terminal)
python demo.py
```
This runs automated tests showing all features.

---

## 🎯 First Things to Try

### In the Gradio Dashboard (http://localhost:7860):

1. **AI Agent Tab:**
   - Query: "What's the current health status of field_A1?"
   - Watch the multi-agent system diagnose and recommend actions

2. **AIOps Tab:**
   - Click "Run AIOps Monitor"
   - See anomaly detection + auto-remediation in action

3. **Sensor Data Tab:**
   - Select a field
   - View temperature, moisture, pH, NPK trends

---

## 📝 .env Configuration

Minimum required in `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=openai/gpt-4o
```

Optional (has defaults):
```bash
ANOMALY_THRESHOLD_TEMP=35.0
ANOMALY_THRESHOLD_MOISTURE=30.0
AUTO_REMEDIATION_ENABLED=true
```

---

## 🧪 Quick Test via API

```bash
# Get dashboard stats
curl http://localhost:8000/api/dashboard/stats

# Query the AI agent
curl -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which fields need irrigation?",
    "field_id": null
  }'

# Trigger AIOps monitoring
curl -X POST http://localhost:8000/api/aiops/monitor

# Get active alerts
curl http://localhost:8000/api/alerts?resolved=false
```

---

## 📚 Documentation Structure

- **README.md** - Complete project guide
- **TESTING.md** - Testing scenarios and validation
- **DEPLOYMENT.md** - AWS production deployment
- **PRESENTATION.md** - Demo script for interviews
- **PROJECT_SUMMARY.md** - Portfolio presentation guide

---

## 🔍 Project Statistics

- **Total Code:** 2,346 lines of Python
- **Documentation:** 2,000+ lines
- **Technologies:** FastAPI, SQLAlchemy, GPT-4, Gradio, Docker
- **Features:** Multi-agent AI, AIOps, cost tracking, auto-remediation
- **Build Time:** 6-8 hours (overnight project)

---

## 💡 What This Demonstrates

✅ **Agentic AI** - Multi-agent orchestration with tool calling  
✅ **AIOps** - Real-time anomaly detection + auto-remediation  
✅ **Full-Stack** - API + database + interactive UI  
✅ **Production-Ready** - Docker, deployment guides, monitoring  
✅ **Domain Expertise** - AgriTech problem solving  

---

## 🐛 Troubleshooting

**"ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

**"OpenRouter API Error"**
- Check your API key in `.env`
- Verify you have credits at https://openrouter.ai/credits

**"No data found"**
```bash
python data/seed_data.py
```

**"Port already in use"**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

---

## 🎯 Next Steps

1. ✅ Get it running locally (follow steps above)
2. 📹 Record a demo video
3. 📸 Take screenshots of dashboard
4. 🚀 Deploy to AWS (see DEPLOYMENT.md)
5. 💼 Add to portfolio
6. 🎤 Prepare demo (see PRESENTATION.md)

---

## 📧 Support

For questions or issues:
1. Check TESTING.md for common scenarios
2. Review API docs at http://localhost:8000/docs
3. See troubleshooting section above

---

**Ready to impress in interviews!** 🚀

Built with ❤️ for demonstrating Agentic AI + AIOps skills.
