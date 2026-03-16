import json
import requests
import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.tools.sensor_tools import SensorTools
import os
from dotenv import load_dotenv

load_dotenv()

class DiagnosticAgent:
    """
    Diagnostic Agent: Analyzes farm data and identifies issues
    Uses GPT-4 through OpenRouter API
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.tools = SensorTools()
        
        # Available function tools
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_latest_sensor_data",
                    "description": "Get the most recent sensor reading for a specific field",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {
                                "type": "string",
                                "description": "The field identifier (e.g., 'field_A1', 'field_B2')"
                            }
                        },
                        "required": ["field_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_soil_health",
                    "description": "Analyze soil health based on NPK levels and pH, get recommendations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {
                                "type": "string",
                                "description": "The field identifier"
                            }
                        },
                        "required": ["field_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_irrigation_efficiency",
                    "description": "Check if irrigation is needed based on soil moisture levels",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {
                                "type": "string",
                                "description": "The field identifier"
                            }
                        },
                        "required": ["field_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_pest_patterns",
                    "description": "Detect potential pest issues based on environmental conditions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {
                                "type": "string",
                                "description": "The field identifier"
                            }
                        },
                        "required": ["field_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_field_history",
                    "description": "Get historical sensor data for trend analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {
                                "type": "string",
                                "description": "The field identifier"
                            },
                            "hours": {
                                "type": "integer",
                                "description": "Number of hours of history to retrieve (default: 24)"
                            }
                        },
                        "required": ["field_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_active_alerts",
                    "description": "Get all active unresolved alerts for a field or all fields",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {
                                "type": "string",
                                "description": "Optional field identifier. If not provided, returns alerts for all fields"
                            }
                        }
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], db: Session) -> Any:
        """Execute a tool function"""
        tool_map = {
            "get_latest_sensor_data": self.tools.get_latest_sensor_data,
            "analyze_soil_health": self.tools.analyze_soil_health,
            "check_irrigation_efficiency": self.tools.check_irrigation_efficiency,
            "detect_pest_patterns": self.tools.detect_pest_patterns,
            "get_field_history": self.tools.get_field_history,
            "get_active_alerts": self.tools.get_active_alerts
        }
        
        if tool_name in tool_map:
            return tool_map[tool_name](db, **arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def diagnose(self, query: str, db: Session, field_id: str = None) -> Dict[str, Any]:
        """
        Main diagnostic function using agentic reasoning
        """
        start_time = time.time()
        tools_used = []
        
        # System prompt for diagnostic agent
        system_prompt = """You are an expert agricultural diagnostic AI agent. Your role is to:
1. Analyze farm sensor data to identify crop health issues
2. Detect anomalies in soil conditions, moisture, temperature, and nutrients
3. Identify pest and disease risks based on environmental patterns
4. Provide detailed diagnostic reports with evidence-based reasoning

When analyzing data:
- Always call relevant tool functions to gather data before making diagnoses
- Consider interactions between multiple factors (e.g., temperature + humidity for disease risk)
- Prioritize issues by severity and urgency
- Provide specific, actionable insights

You have access to real-time sensor data tools. Use them to gather comprehensive information before responding.
"""

        # Enhance query with field context if provided
        if field_id:
            query = f"[Field: {field_id}] {query}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        # Iterative agentic loop - allow up to 5 tool calls
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            try:
                # Call OpenRouter API
                response = requests.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "tools": self.available_tools,
                        "tool_choice": "auto"
                    },
                    timeout=30
                )
                
                response.raise_for_status()
                result = response.json()
                
                assistant_message = result["choices"][0]["message"]
                messages.append(assistant_message)
                
                # Check if agent wants to use tools
                if assistant_message.get("tool_calls"):
                    # Execute each tool call
                    for tool_call in assistant_message["tool_calls"]:
                        function_name = tool_call["function"]["name"]
                        function_args = json.loads(tool_call["function"]["arguments"])
                        
                        # Execute the tool
                        tool_result = self.execute_tool(function_name, function_args, db)
                        tools_used.append(function_name)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(tool_result)
                        })
                    
                    iteration += 1
                else:
                    # No more tool calls, agent has final response
                    final_response = assistant_message.get("content", "")
                    execution_time = time.time() - start_time
                    
                    return {
                        "response": final_response,
                        "tools_used": list(set(tools_used)),
                        "execution_time": round(execution_time, 2),
                        "iterations": iteration
                    }
                    
            except Exception as e:
                return {
                    "response": f"Error in diagnostic agent: {str(e)}",
                    "tools_used": tools_used,
                    "execution_time": time.time() - start_time,
                    "error": True
                }
        
        # Max iterations reached
        execution_time = time.time() - start_time
        return {
            "response": "Diagnostic analysis completed. Maximum tool iterations reached.",
            "tools_used": list(set(tools_used)),
            "execution_time": round(execution_time, 2),
            "iterations": iteration
        }
