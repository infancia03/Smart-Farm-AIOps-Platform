from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agents.diagnostic_agent import DiagnosticAgent
from app.agents.action_agent import ActionAgent
from app.database import AgentLog
import time
import json

class OrchestratorAgent:
    """
    Orchestrator Agent: Coordinates diagnostic and action agents
    Implements multi-agent workflow
    """
    
    def __init__(self):
        self.diagnostic_agent = DiagnosticAgent()
        self.action_agent = ActionAgent()
    
    def process_query(self, query: str, db: Session, field_id: str = None, auto_remediate: bool = True) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system
        
        Workflow:
        1. Diagnostic agent analyzes the situation
        2. If issues found, action agent plans remediation
        3. Log all agent activities
        4. Return comprehensive response
        """
        start_time = time.time()
        
        # Step 1: Diagnostic Phase
        print(f"🔍 Diagnostic Agent analyzing query: {query[:100]}...")
        diagnostic_result = self.diagnostic_agent.diagnose(query, db, field_id)
        
        # Log diagnostic agent activity
        diagnostic_log = AgentLog(
            agent_type="diagnostic",
            query=query,
            response=diagnostic_result.get("response", ""),
            tools_used=json.dumps(diagnostic_result.get("tools_used", [])),
            execution_time=diagnostic_result.get("execution_time", 0)
        )
        db.add(diagnostic_log)
        db.commit()
        
        # Step 2: Check if remediation is needed
        action_result = None
        
        # Simple heuristic: if diagnostic mentions issues, trigger action agent
        diagnostic_text = diagnostic_result.get("response", "").lower()
        needs_action = any(keyword in diagnostic_text for keyword in [
            "deficient", "low", "high", "critical", "urgent", "risk", 
            "issue", "problem", "excess", "insufficient", "needed"
        ])
        
        if needs_action and auto_remediate and field_id:
            print(f"⚡ Action Agent planning remediation for field {field_id}...")
            action_result = self.action_agent.plan_and_execute(
                diagnostic_info=diagnostic_result.get("response", ""),
                field_id=field_id,
                db=db,
                auto_execute=True
            )
            
            # Log action agent activity
            action_log = AgentLog(
                agent_type="action",
                query=f"Remediation for: {query[:100]}",
                response=action_result.get("response", ""),
                tools_used=json.dumps([a["action"] for a in action_result.get("actions_taken", [])]),
                execution_time=action_result.get("execution_time", 0)
            )
            db.add(action_log)
            db.commit()
        
        total_time = time.time() - start_time
        
        # Step 3: Compile comprehensive response
        response = {
            "orchestrator_summary": self._generate_summary(diagnostic_result, action_result),
            "diagnostic_phase": {
                "response": diagnostic_result.get("response", ""),
                "tools_used": diagnostic_result.get("tools_used", []),
                "execution_time": diagnostic_result.get("execution_time", 0)
            },
            "action_phase": action_result if action_result else {
                "message": "No remediation actions needed or auto-remediation disabled"
            },
            "total_execution_time": round(total_time, 2),
            "field_id": field_id
        }
        
        return response
    
    def _generate_summary(self, diagnostic_result: Dict, action_result: Dict = None) -> str:
        """Generate executive summary of multi-agent workflow"""
        summary = f"**Diagnostic Summary:**\n{diagnostic_result.get('response', 'No diagnostic information')[:300]}...\n\n"
        
        if action_result:
            summary += f"**Actions Taken:** {action_result.get('total_actions', 0)} remediation actions executed\n"
            summary += f"**Total Cost:** ₹{action_result.get('total_cost_inr', 0)}\n\n"
            
            for action in action_result.get('actions_taken', []):
                summary += f"- {action['action']}: {action['result'].get('action', 'N/A')}\n"
        
        return summary
    
    def get_field_recommendations(self, field_id: str, db: Session) -> Dict[str, Any]:
        """Get comprehensive recommendations for a specific field"""
        query = f"Provide a comprehensive health assessment and recommendations for field {field_id}. Include soil health, irrigation needs, pest risks, and nutrient status."
        
        return self.process_query(query, db, field_id, auto_remediate=False)
