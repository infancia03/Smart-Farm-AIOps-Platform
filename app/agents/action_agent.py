import json
import requests
import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database import Alert, RemediationLog
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class ActionAgent:
    """
    Action Agent: Plans and executes remediation actions
    Uses GPT-4 through OpenRouter API
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Available action tools
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "trigger_irrigation",
                    "description": "Activate irrigation system for a specific field",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {"type": "string", "description": "Field identifier"},
                            "water_amount_liters": {"type": "number", "description": "Amount of water in liters"},
                            "duration_minutes": {"type": "number", "description": "Irrigation duration in minutes"}
                        },
                        "required": ["field_id", "water_amount_liters"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_fertilizer",
                    "description": "Schedule fertilizer application",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {"type": "string"},
                            "fertilizer_type": {"type": "string", "enum": ["nitrogen", "phosphorus", "potassium", "npk_balanced"]},
                            "amount_kg": {"type": "number", "description": "Amount in kilograms"}
                        },
                        "required": ["field_id", "fertilizer_type", "amount_kg"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_farmer_alert",
                    "description": "Send alert notification to farmer via SMS/WhatsApp",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {"type": "string"},
                            "message": {"type": "string", "description": "Alert message to send"},
                            "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                        },
                        "required": ["field_id", "message", "urgency"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "adjust_ph_level",
                    "description": "Apply lime or sulfur to adjust soil pH",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {"type": "string"},
                            "adjustment_type": {"type": "string", "enum": ["increase_ph_lime", "decrease_ph_sulfur"]},
                            "amount_kg": {"type": "number"}
                        },
                        "required": ["field_id", "adjustment_type", "amount_kg"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "activate_cooling_system",
                    "description": "Activate shade nets or cooling system for temperature control",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {"type": "string"},
                            "cooling_method": {"type": "string", "enum": ["shade_net", "misting", "both"]},
                            "duration_hours": {"type": "number"}
                        },
                        "required": ["field_id", "cooling_method"]
                    }
                }
            }
        ]
    
    def execute_action(self, action_name: str, arguments: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Execute an action (simulated for demo)"""
        
        field_id = arguments.get("field_id")
        
        # Simulate action execution with cost calculation
        action_results = {
            "trigger_irrigation": {
                "success": True,
                "action": f"Irrigation activated for {arguments.get('water_amount_liters')}L",
                "cost": arguments.get('water_amount_liters', 0) * 0.05,  # ₹0.05/liter
                "details": f"Duration: {arguments.get('duration_minutes', 30)} minutes"
            },
            "apply_fertilizer": {
                "success": True,
                "action": f"Fertilizer application scheduled: {arguments.get('fertilizer_type')}",
                "cost": arguments.get('amount_kg', 0) * 45,  # ₹45/kg avg
                "details": f"Amount: {arguments.get('amount_kg')}kg, Type: {arguments.get('fertilizer_type')}"
            },
            "send_farmer_alert": {
                "success": True,
                "action": "Alert sent to farmer",
                "cost": 0.50,  # ₹0.50 per SMS
                "details": f"Urgency: {arguments.get('urgency')}, Message: {arguments.get('message')[:50]}..."
            },
            "adjust_ph_level": {
                "success": True,
                "action": f"pH adjustment scheduled: {arguments.get('adjustment_type')}",
                "cost": arguments.get('amount_kg', 0) * 25,  # ₹25/kg
                "details": f"Amount: {arguments.get('amount_kg')}kg"
            },
            "activate_cooling_system": {
                "success": True,
                "action": f"Cooling system activated: {arguments.get('cooling_method')}",
                "cost": arguments.get('duration_hours', 2) * 15,  # ₹15/hour
                "details": f"Duration: {arguments.get('duration_hours', 2)} hours"
            }
        }
        
        result = action_results.get(action_name, {
            "success": False,
            "action": f"Unknown action: {action_name}",
            "cost": 0,
            "details": "Action not found"
        })
        
        # Log the remediation action
        log_entry = RemediationLog(
            alert_id=arguments.get("alert_id", 0),
            field_id=field_id,
            action_type=action_name,
            action_details=json.dumps(arguments),
            success=result["success"],
            cost_estimate=result["cost"]
        )
        db.add(log_entry)
        db.commit()
        
        return result
    
    def plan_and_execute(self, diagnostic_info: str, field_id: str, db: Session, auto_execute: bool = True) -> Dict[str, Any]:
        """
        Plan and execute remediation actions based on diagnostic information
        """
        start_time = time.time()
        actions_taken = []
        
        system_prompt = """You are an agricultural action planning AI agent. Your role is to:
1. Analyze diagnostic information about farm issues
2. Plan appropriate remediation actions
3. Execute actions automatically when authorized
4. Prioritize actions by urgency and cost-effectiveness

Available actions:
- trigger_irrigation: For low soil moisture
- apply_fertilizer: For nutrient deficiencies
- send_farmer_alert: For critical issues requiring human intervention
- adjust_ph_level: For pH imbalances
- activate_cooling_system: For excessive heat

Always consider:
- Cost-effectiveness of interventions
- Urgency of the issue
- Potential side effects of actions
- Resource availability

Execute necessary actions using the available tools.
"""

        query = f"""Field {field_id} diagnostic report:

{diagnostic_info}

Please analyze this diagnostic information and execute appropriate remediation actions. Auto-execution is {'ENABLED' if auto_execute else 'DISABLED'}.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            try:
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
                
                if assistant_message.get("tool_calls") and auto_execute:
                    for tool_call in assistant_message["tool_calls"]:
                        function_name = tool_call["function"]["name"]
                        function_args = json.loads(tool_call["function"]["arguments"])
                        function_args["field_id"] = field_id  # Ensure field_id is set
                        
                        # Execute the action
                        action_result = self.execute_action(function_name, function_args, db)
                        actions_taken.append({
                            "action": function_name,
                            "parameters": function_args,
                            "result": action_result
                        })
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(action_result)
                        })
                    
                    iteration += 1
                else:
                    # Final response
                    final_response = assistant_message.get("content", "")
                    execution_time = time.time() - start_time
                    
                    total_cost = sum(a["result"].get("cost", 0) for a in actions_taken)
                    
                    return {
                        "response": final_response,
                        "actions_taken": actions_taken,
                        "total_actions": len(actions_taken),
                        "total_cost_inr": round(total_cost, 2),
                        "execution_time": round(execution_time, 2)
                    }
                    
            except Exception as e:
                return {
                    "response": f"Error in action agent: {str(e)}",
                    "actions_taken": actions_taken,
                    "execution_time": time.time() - start_time,
                    "error": True
                }
        
        execution_time = time.time() - start_time
        total_cost = sum(a["result"].get("cost", 0) for a in actions_taken)
        
        return {
            "response": "Action planning completed.",
            "actions_taken": actions_taken,
            "total_actions": len(actions_taken),
            "total_cost_inr": round(total_cost, 2),
            "execution_time": round(execution_time, 2)
        }
