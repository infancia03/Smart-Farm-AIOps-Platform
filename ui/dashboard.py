import gradio as gr
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json

# API base URL (update if running on different host/port)
API_BASE_URL = "http://localhost:8000"

def get_dashboard_stats():
    """Fetch dashboard statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard/stats")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return {"error": str(e)}

def query_agent(question, field_id):
    """Query the agentic AI system"""
    try:
        payload = {
            "query": question,
            "field_id": field_id if field_id else None
        }
        response = requests.post(f"{API_BASE_URL}/api/agent/query", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            # Format the response nicely
            output = f"## 🤖 Agent Response\n\n"
            output += f"{result['orchestrator_summary']}\n\n"
            output += f"**Diagnostic Phase:**\n{result['diagnostic_phase']['response'][:500]}...\n\n"
            
            if "actions_taken" in result.get("action_phase", {}):
                output += f"**Actions Executed:** {result['action_phase']['total_actions']}\n"
                output += f"**Total Cost:** ₹{result['action_phase']['total_cost_inr']}\n\n"
            
            output += f"⏱️ Execution Time: {result['total_execution_time']}s"
            
            return output
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error querying agent: {str(e)}"

def get_field_sensors(field_id, hours=24):
    """Get sensor data for visualization"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/sensors/data/{field_id}?hours={hours}")
        if response.status_code == 200:
            data = response.json()
            if not data:
                return "No data available for this field"
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Create visualization
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle(f'Sensor Data - {field_id} (Last {hours}h)', fontsize=16)
            
            # Temperature
            axes[0, 0].plot(df['timestamp'], df['temperature'], 'r-', linewidth=2)
            axes[0, 0].set_title('Temperature (°C)')
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Soil Moisture
            axes[0, 1].plot(df['timestamp'], df['soil_moisture'], 'b-', linewidth=2)
            axes[0, 1].axhline(y=30, color='r', linestyle='--', label='Critical')
            axes[0, 1].set_title('Soil Moisture (%)')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # pH Level
            axes[1, 0].plot(df['timestamp'], df['ph_level'], 'g-', linewidth=2)
            axes[1, 0].axhline(y=6.0, color='orange', linestyle='--', alpha=0.5)
            axes[1, 0].axhline(y=7.5, color='orange', linestyle='--', alpha=0.5)
            axes[1, 0].set_title('pH Level')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # NPK Nutrients
            axes[1, 1].plot(df['timestamp'], df['nitrogen'], 'purple', label='N', linewidth=2)
            axes[1, 1].plot(df['timestamp'], df['phosphorus'], 'orange', label='P', linewidth=2)
            axes[1, 1].plot(df['timestamp'], df['potassium'], 'brown', label='K', linewidth=2)
            axes[1, 1].set_title('NPK Levels (ppm)')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            return fig
        else:
            return f"Error fetching data: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_active_alerts():
    """Get active alerts"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/alerts?resolved=false")
        if response.status_code == 200:
            alerts = response.json()
            if not alerts:
                return "✅ No active alerts"
            
            output = "## 🚨 Active Alerts\n\n"
            for alert in alerts[:10]:  # Show top 10
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(alert['severity'], "⚪")
                
                output += f"{severity_emoji} **{alert['field_id']}** - {alert['alert_type']}\n"
                output += f"   {alert['message']}\n"
                output += f"   Auto-remediation: {'✅ Applied' if alert['auto_remediation_applied'] else '❌ Not applied'}\n\n"
            
            return output
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def run_aiops_monitor(field_id=None):
    """Manually trigger AIOps monitoring"""
    try:
        params = {"field_id": field_id} if field_id else {}
        response = requests.post(f"{API_BASE_URL}/api/aiops/monitor", params=params)
        
        if response.status_code == 200:
            result = response.json()
            output = f"## 🔍 AIOps Monitoring Results\n\n"
            output += f"**Anomalies Detected:** {result['anomalies_detected']}\n"
            output += f"**Alerts Created:** {result['alerts_created']}\n\n"
            
            if "auto_remediation" in result:
                remediation = result['auto_remediation']
                output += f"**Auto-Remediation Executed:** {remediation['remediations_executed']} actions\n"
                output += f"**Total Cost:** ₹{remediation['total_cost_inr']}\n"
            
            return output
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_trend_analysis(field_id):
    """Get trend analysis and predictions"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/aiops/trends/{field_id}")
        if response.status_code == 200:
            result = response.json()
            output = f"## 📈 Trend Analysis - {field_id}\n\n"
            output += f"**Temperature Trend:** {result['temperature_trend']} (Current: {result['current_temp']}°C)\n"
            output += f"**Moisture Trend:** {result['moisture_trend']} (Current: {result['current_moisture']}%)\n\n"
            
            if result['predictions']:
                output += "### 🔮 Predictions:\n"
                for pred in result['predictions']:
                    output += f"- **{pred['type']}** in ~{pred['estimated_time_hours']:.1f}h (Confidence: {pred['confidence']})\n"
            else:
                output += "✅ No issues predicted in the near term\n"
            
            return output
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio Interface
with gr.Blocks(title="Smart Farm AIOps Platform", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🌾 Smart Farm AIOps Platform
    ### AI-Powered Agricultural Monitoring & Auto-Remediation
    
    Multi-agent system with diagnostic AI, action AI, and AIOps monitoring
    """)
    
    with gr.Tabs():
        # Tab 1: Dashboard Overview
        with gr.Tab("📊 Dashboard"):
            gr.Markdown("## System Overview")
            refresh_btn = gr.Button("🔄 Refresh Stats")
            stats_output = gr.Markdown()
            
            def show_stats():
                stats = get_dashboard_stats()
                if stats:
                    return f"""
### Key Metrics
- **Total Fields:** {stats.get('total_fields', 0)}
- **Active Alerts:** {stats.get('active_alerts', 0)} (Critical: {stats.get('critical_alerts', 0)})
- **Recent Readings (1h):** {stats.get('recent_readings_1h', 0)}
- **Auto-Remediations (24h):** {stats.get('remediation_summary', {}).get('total_actions_24h', 0)}
- **Remediation Cost (24h):** ₹{stats.get('remediation_summary', {}).get('total_cost_24h', 0)}

**Active Fields:** {', '.join(stats.get('field_ids', []))}
                    """
                return "Error loading stats"
            
            refresh_btn.click(show_stats, outputs=stats_output)
            demo.load(show_stats, outputs=stats_output)
        
        # Tab 2: Agentic AI Query
        with gr.Tab("🤖 AI Agent"):
            gr.Markdown("## Query the Multi-Agent System")
            
            with gr.Row():
                agent_query = gr.Textbox(
                    label="Ask a question",
                    placeholder="e.g., What's the current health status of field_A1?",
                    lines=2
                )
                agent_field = gr.Dropdown(
                    choices=["", "field_A1", "field_A2", "field_B1", "field_B2", "field_C1"],
                    label="Specific Field (optional)",
                    value=""
                )
            
            agent_submit = gr.Button("🚀 Query Agent", variant="primary")
            agent_output = gr.Markdown()
            
            # Example queries
            gr.Markdown("### Example Queries:")
            example_queries = [
                ["What fields need irrigation right now?", ""],
                ["Analyze soil health for field_A1", "field_A1"],
                ["Show me pest risk patterns", ""],
                ["What's causing the low moisture in field_B1?", "field_B1"]
            ]
            
            gr.Examples(
                examples=example_queries,
                inputs=[agent_query, agent_field]
            )
            
            agent_submit.click(
                query_agent,
                inputs=[agent_query, agent_field],
                outputs=agent_output
            )
        
        # Tab 3: Sensor Monitoring
        with gr.Tab("📡 Sensor Data"):
            gr.Markdown("## Real-Time Sensor Monitoring")
            
            with gr.Row():
                sensor_field = gr.Dropdown(
                    choices=["field_A1", "field_A2", "field_B1", "field_B2", "field_C1"],
                    label="Select Field",
                    value="field_A1"
                )
                sensor_hours = gr.Slider(
                    minimum=6,
                    maximum=48,
                    value=24,
                    step=6,
                    label="Time Range (hours)"
                )
            
            sensor_btn = gr.Button("📊 Load Sensor Data")
            sensor_plot = gr.Plot()
            
            sensor_btn.click(
                get_field_sensors,
                inputs=[sensor_field, sensor_hours],
                outputs=sensor_plot
            )
        
        # Tab 4: AIOps Monitoring
        with gr.Tab("🔍 AIOps"):
            gr.Markdown("## Automated Operations & Monitoring")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🚨 Active Alerts")
                    alerts_btn = gr.Button("Refresh Alerts")
                    alerts_output = gr.Markdown()
                    
                    alerts_btn.click(get_active_alerts, outputs=alerts_output)
                    demo.load(get_active_alerts, outputs=alerts_output)
                
                with gr.Column():
                    gr.Markdown("### 🔍 Manual Monitoring Trigger")
                    monitor_field = gr.Dropdown(
                        choices=["All Fields", "field_A1", "field_A2", "field_B1", "field_B2", "field_C1"],
                        label="Field to Monitor",
                        value="All Fields"
                    )
                    monitor_btn = gr.Button("▶️ Run AIOps Monitor", variant="primary")
                    monitor_output = gr.Markdown()
                    
                    def monitor_wrapper(field_choice):
                        field = None if field_choice == "All Fields" else field_choice
                        return run_aiops_monitor(field)
                    
                    monitor_btn.click(
                        monitor_wrapper,
                        inputs=monitor_field,
                        outputs=monitor_output
                    )
            
            gr.Markdown("### 📈 Trend Analysis & Predictions")
            trend_field = gr.Dropdown(
                choices=["field_A1", "field_A2", "field_B1", "field_B2", "field_C1"],
                label="Select Field",
                value="field_A1"
            )
            trend_btn = gr.Button("🔮 Analyze Trends")
            trend_output = gr.Markdown()
            
            trend_btn.click(
                get_trend_analysis,
                inputs=trend_field,
                outputs=trend_output
            )
    
    gr.Markdown("""
    ---
    ### 🎯 Features:
    - **Multi-Agent AI:** Diagnostic + Action agents working together
    - **AIOps:** Real-time anomaly detection & auto-remediation
    - **Natural Language:** Query your farm data in plain English
    - **Cost Tracking:** Every action has estimated cost in ₹
    """)

if __name__ == "__main__":
    print("🚀 Starting Smart Farm AIOps Dashboard...")
    print("📍 Make sure the FastAPI server is running on http://localhost:8000")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
