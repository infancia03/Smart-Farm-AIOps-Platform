# Smart Farm AIOps Platform

**AI-Powered Agricultural Monitoring & Auto-Remediation System**

A platform that combines **Agentic AI** and **AIOps** to automate agricultural monitoring, anomaly detection, and corrective actions across smart farm sensor networks. Built with FastAPI, NVIDIA Nemotron 3 Super (via OpenRouter), and a multi-agent orchestration architecture.

---

## Overview

Traditional farm monitoring relies on manual inspection and reactive intervention. This platform addresses that gap by deploying AI agents that continuously analyze sensor data, detect anomalies, and autonomously execute remediation workflows — reducing the need for manual oversight and enabling faster response to field conditions.

---

## Key Features

### Multi-Agent AI System
- **Diagnostic Agent** — Analyzes farm health using tool-calling (soil analysis, irrigation checks, pest detection) powered by NVIDIA Nemotron 3 Super
- **Action Agent** — Plans and executes remediation strategies (irrigation scheduling, fertilization, alerting)
- **Orchestrator** — Coordinates both agents for end-to-end automation with iterative reasoning (up to 5 tool calls per query)

### AIOps Engine
- Real-time anomaly detection across multi-field sensor streams
- Predictive trend analysis with configurable thresholds (temperature, moisture, pH, NPK)
- Auto-remediation engine that triggers corrective actions upon alert creation
- Cost tracking per action (₹ per litre/kg/hour) for operational budgeting

### Natural Language Interface
- Plain-English queries: *"Which fields need irrigation right now?"*
- Function calling and tool use via NVIDIA Nemotron 3 Super
- Context-aware reasoning across multiple data sources simultaneously

### Production-Ready Stack
- Async FastAPI REST API with background task processing
- SQLAlchemy ORM with SQLite (configurable for MySQL/PostgreSQL)
- Gradio interactive dashboard for real-time visualization
- Systemd service management with auto-restart and health monitoring
- Nginx reverse proxy with SSL-ready configuration

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Gradio Dashboard UI                      │
│          (Natural Language Queries + Visualizations)         │
└─────────────────────┬────────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────────┐
│                    FastAPI REST API                           │
│   /api/agent/query | /api/aiops/monitor | /api/sensors/data  │
└──────┬───────────────────────────────┬──────────────┬────────┘
       │                               │              │
┌──────▼─────────┐          ┌──────────▼───────┐  ┌──▼───────┐
│  Orchestrator  │          │   AIOps Engine   │  │ Database │
│     Agent      │          │                  │  │ SQLite / │
│                │          │ ┌──────────────┐ │  │ MySQL    │
│ ┌────────────┐ │          │ │  Anomaly     │ │  └──────────┘
│ │ Diagnostic │ │          │ │  Detector    │ │
│ │   Agent    │◄├──────────┤ └──────┬───────┘ │
│ │ (Nemotron) │ │          │        │          │
│ └─────┬──────┘ │          │ ┌──────▼────────┐ │
│       │        │          │ │ Auto-         │ │
│ ┌─────▼──────┐ │          │ │ Remediation   │ │
│ │   Action   │ │          │ │ Engine        │ │
│ │   Agent    │ │          │ └───────────────┘ │
│ │ (Nemotron) │ │          └──────────────────-┘
│ └────────────┘ │
└────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  Sensor Tools (Function Calling)             │
│  • analyze_soil_health()    • check_irrigation_efficiency()  │
│  • detect_pest_patterns()   • get_field_history()            │
│  • trigger_irrigation()     • apply_fertilizer()             │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI (async) |
| AI Model | NVIDIA Nemotron 3 Super via OpenRouter |
| Dashboard | Gradio |
| ORM | SQLAlchemy |
| Database | SQLite (MySQL-ready) |
| Process Management | systemd |
| Reverse Proxy | Nginx |
| Containerization | Docker + Docker Compose |
| Language | Python 3.11 |

---

## Getting Started

### Prerequisites
- Python 3.9+
- OpenRouter API Key with access to NVIDIA Nemotron 3 Super

### 1. Installation

```bash
git clone https://github.com/infancia03/Smart-Farm-AIOps-Platform.git
cd Smart-Farm-AIOps-Platform
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
cp .env.example .env
nano .env
```

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=nvidia/nemotron-super-3
AUTO_REMEDIATION_ENABLED=true
```

### 3. Generate Sample Data

```bash
python data/seed_data.py
```

Creates 48 hours of sensor data across 5 fields with realistic patterns and injected anomalies.

### 4. Start the API Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 5. Launch the Dashboard

```bash
python ui/dashboard.py
```

Dashboard: `http://localhost:7860`

---

## API Reference

### Sensors
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/sensors/data` | Submit a sensor reading |
| GET | `/api/sensors/data/{field_id}` | Get historical readings |
| GET | `/api/sensors/latest/{field_id}` | Get latest reading |

### Agentic AI
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/agent/query` | Natural language query |
| GET | `/api/agent/recommendations/{field_id}` | Get AI recommendations |

### AIOps
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/aiops/monitor` | Trigger anomaly detection |
| GET | `/api/aiops/trends/{field_id}` | Trend analysis & predictions |

### Alerts & Remediation
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/alerts` | List alerts with filters |
| PATCH | `/api/alerts/{id}/resolve` | Resolve an alert |
| POST | `/api/remediation/execute` | Trigger manual remediation |
| GET | `/api/remediation/history` | View remediation logs |

---

## Usage Examples

### Natural Language Query

```bash
curl -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Which fields have nitrogen deficiency?", "field_id": null}'
```

The diagnostic agent scans all fields, identifies NPK anomalies, and the action agent returns a prioritized fertilization plan with cost estimates.

### Trigger AIOps Monitor

```bash
curl -X POST http://localhost:8000/api/aiops/monitor \
  -H "Content-Type: application/json" \
  -d '{"field_id": "field_A1"}'
```

Detects anomalies, creates alerts, and auto-triggers remediation if `AUTO_REMEDIATION_ENABLED=true`.

### Trend Analysis

```bash
curl http://localhost:8000/api/aiops/trends/field_A1?hours=24
```

Returns temperature/moisture trends, predicted irrigation needs with ETA, and confidence scores.

---

## Project Structure

```
smart-farm-aiops/
├── app/
│   ├── agents/
│   │   ├── diagnostic_agent.py    # AI diagnostic reasoning
│   │   ├── action_agent.py        # Remediation planning
│   │   └── orchestrator.py        # Multi-agent coordinator
│   ├── aiops/
│   │   ├── anomaly_detector.py    # Real-time anomaly detection
│   │   └── auto_remediation.py    # Auto-fix engine
│   ├── tools/
│   │   └── sensor_tools.py        # Function calling tools
│   ├── database.py                # SQLAlchemy models
│   ├── models.py                  # Pydantic schemas
│   └── main.py                    # FastAPI application
├── data/
│   └── seed_data.py               # Sample data generator
├── ui/
│   └── dashboard.py               # Gradio interface
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Deployment

### Docker

```bash
docker-compose up -d
```

### EC2 with systemd

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full production setup including Nginx reverse proxy, SSL configuration, and systemd service files.

---

## Future Roadmap

- [ ] ESP32/MQTT integration for real hardware sensors
- [ ] WhatsApp/SMS alert delivery via Twilio
- [ ] Custom ML models for crop-specific anomaly thresholds
- [ ] Multi-crop support with agronomic knowledge base
- [ ] Prometheus metrics endpoint + Grafana dashboard
- [ ] React Native mobile dashboard

---

## Acknowledgements

Built with [FastAPI](https://fastapi.tiangolo.com), [OpenRouter](https://openrouter.ai), [Gradio](https://gradio.app), [SQLAlchemy](https://sqlalchemy.org), and [NVIDIA Nemotron 3 Super](https://build.nvidia.com/nvidia/nemotron-super-49b-v1).
