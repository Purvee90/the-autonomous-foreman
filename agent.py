# import os
# import json
# import logging
# from dotenv import load_dotenv

# from google.adk.agents import Agent, SequentialAgent
# from google.adk.tools.tool_context import ToolContext

# load_dotenv()

# model_name = os.getenv("MODEL", "gemini-2.0-flash")

# # --- MCP Toolsets ---
# # MCPToolset instances are passed directly into the agent's tools= list.
# # ADK handles calling the remote MCP tools internally — you do NOT call
# # bigquery_toolset.call_tool() yourself. That method does not exist.
# from tools import get_calendar_mcp_toolset, get_bigquery_mcp_toolset

# calendar_toolset = get_calendar_mcp_toolset()
# bigquery_toolset = get_bigquery_mcp_toolset()


# # --- State-management helper tools ---
# # These plain Python functions read/write ADK shared state so each
# # sub-agent can pick up where the previous one left off.

# def save_telemetry_to_state(tool_context: ToolContext, station_id: str) -> dict:
#     """
#     Saves the station_id into shared ADK state so downstream agents
#     can reference it without re-querying. The actual BigQuery query
#     is handled by the bigquery_toolset MCP tool (analyze_wind_telemetry).
#     """
#     tool_context.state["station_id"] = station_id
#     return {"status": "ok", "station_id": station_id}


# def save_schedule_to_state(
#     tool_context: ToolContext,
#     decision: str,
#     event_link: str,
#     scheduled_start: str,
# ) -> dict:
#     """
#     Called by the Policy Agent after the Calendar MCP creates an event.
#     Persists scheduling details so the Alert Agent can read them.
#     """
#     tool_context.state["maintenance_decision"] = decision
#     tool_context.state["event_link"] = event_link
#     tool_context.state["scheduled_time"] = scheduled_start
#     return {"status": "saved"}


# def build_alert_summary(tool_context: ToolContext) -> dict:
#     """
#     Final step — reads everything from state and returns a summary dict.
#     No external calls needed here.
#     """
#     return {
#         "status": "success",
#         "summary": (
#             f"Station {tool_context.state.get('station_id')} | "
#             f"Severity: {tool_context.state.get('severity', 'Unknown')} | "
#             f"Action: {tool_context.state.get('maintenance_decision', 'N/A')} | "
#             f"Calendar: {tool_context.state.get('event_link', 'N/A')}"
#         )
#     }


# # --- Sub-Agents ---

# anomaly_agent = Agent(
#     name="Anomaly_Detection_Agent",
#     model=model_name,
#     description="Queries wind telemetry from BigQuery and detects anomalies.",
#     instruction=(
#         "You analyze turbine sensor data. "
#         "Step 1: Call `save_telemetry_to_state` with the station_id to register the station. "
#         "Step 2: Call the `analyze_wind_telemetry` MCP tool with the station_id to get live readings. "
#         "Step 3: Save the returned severity and diagnostic into session state. "
#         "Do not skip any step."
#     ),
#     # FIX: bigquery_toolset goes HERE — the agent that uses it.
#     # The MCP tool 'analyze_wind_telemetry' is exposed by the toolset automatically.
#     tools=[save_telemetry_to_state, bigquery_toolset],
# )

# policy_agent = Agent(
#     name="Maintenance_Policy_Agent",
#     model=model_name,
#     description="Schedules maintenance by creating a Google Calendar event.",
#     instruction=(
#         "You handle scheduling. "
#         "Read 'severity' and 'station_id' from the session state. "
#         "Call the `schedule_maintenance_event` MCP tool with severity, station_id, and diagnostic. "
#         "Then call `save_schedule_to_state` with the decision, event_link, and scheduled_start returned. "
#         "Never ask the user for input — use only what is in state."
#     ),
#     # FIX: calendar_toolset goes HERE — the agent that uses it.
#     tools=[save_schedule_to_state, calendar_toolset],
# )

# alert_agent = Agent(
#     name="Alert_Strategy_Agent",
#     model=model_name,
#     description="Finalizes the workflow and produces a dispatch summary.",
#     instruction=(
#         "You are the final dispatcher. "
#         "Read maintenance_decision and event_link from state. "
#         "Call `build_alert_summary` to produce the final report. "
#         "Then present the summary clearly to the user."
#     ),
#     tools=[build_alert_summary],
# )


# # --- Coordinator ---

# primary_coordinator = SequentialAgent(
#     name="Autonomous_Foreman_Coordinator",
#     description="Runs detect → schedule → alert in sequence.",
#     # FIX: correct param is sub_agents=, not agents=
#     sub_agents=[anomaly_agent, policy_agent, alert_agent],
# )


# # --- Root Agent ---

# root_agent = Agent(
#     name="predictive_maintenance_root",
#     model=model_name,
#     description="Entry point for the Predictive Maintenance system.",
#     instruction=(
#         "You are the Autonomous Foreman. "
#         "When the user provides a station ID or asks about turbine health, "
#         "immediately delegate to Autonomous_Foreman_Coordinator. "
#         "Once it finishes, summarize: what was detected, when maintenance is scheduled, and what alert was sent."
#     ),
#     sub_agents=[primary_coordinator],
# )


# # --- Local test runner ---
# if __name__ == "__main__":
#     import asyncio
#     from google.adk.runners import Runner
#     from google.adk.sessions import InMemorySessionService
#     from google.genai import types

#     async def main():
#         print("\n🚀 Starting local agent test")
#         print(f"   BigQuery MCP : {os.getenv('BIGQUERY_MCP_URL')}")
#         print(f"   Calendar MCP : {os.getenv('CALENDAR_MCP_URL')}\n")

#         session_service = InMemorySessionService()
#         session = await session_service.create_session(
#             app_name="maintenance_app",
#             user_id="local_test",
#         )

#         runner = Runner(
#             agent=root_agent,
#             app_name="maintenance_app",
#             session_service=session_service,
#         )

#         user_prompt = "Run a health check on station 722530"
#         print(f"User: {user_prompt}\n")

#         content = types.Content(
#             role="user",
#             parts=[types.Part(text=user_prompt)]
#         )

#         async for event in runner.run_async(
#             user_id="local_test",
#             session_id=session.id,
#             new_message=content,
#         ):
#             if event.is_final_response():
#                 print("✅ Agent response:")
#                 print(event.content.parts[0].text)

#     asyncio.run(main())
import sys
import os
import json
import asyncio
from dotenv import load_dotenv

# Force the ADK to look in the current folder for tools.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

model_name = os.getenv("MODEL", "gemini-2.0-flash")

# --- MCP Toolsets ---
from tools import get_bigquery_mcp_toolset

# Only initialize the BigQuery toolset
bigquery_toolset = get_bigquery_mcp_toolset()

# --- State Management Tools ---
def save_analysis_to_state(tool_context: ToolContext, station_id: str, severity: str, diagnostic: str) -> dict:
    """Saves the BigQuery anomaly analysis results so downstream agents can use them."""
    tool_context.state["station_id"] = station_id
    tool_context.state["severity"] = severity
    tool_context.state["diagnostic"] = diagnostic
    return {"status": "success", "message": f"Saved {station_id} with severity {severity}"}

def save_decision_to_state(tool_context: ToolContext, decision: str) -> dict:
    """Persists the maintenance policy decision for the final dispatcher."""
    tool_context.state["maintenance_decision"] = decision
    return {"status": "saved"}

def build_alert_summary(tool_context: ToolContext) -> dict:
    """Reads final state and returns the summary."""
    return {
        "status": "success",
        "summary": (
            f"Station {tool_context.state.get('station_id')} | "
            f"Severity: {tool_context.state.get('severity', 'Unknown')} | "
            f"Diagnostic: {tool_context.state.get('diagnostic', 'None')} | "
            f"Action Required: {tool_context.state.get('maintenance_decision', 'N/A')}"
        )
    }

# --- Sub-Agents ---
anomaly_agent = Agent(
    name="Anomaly_Detection_Agent",
    model=model_name,
    description="Queries wind telemetry from BigQuery and detects anomalies.",
    instruction=(
        "You analyze turbine sensor data. "
        "Step 1: Call the `analyze_wind_telemetry` MCP tool with the requested station_id. "
        "Step 2: Read the JSON response to find the severity and diagnostic. "
        "Step 3: Call `save_analysis_to_state` with the station_id, severity, and diagnostic. "
        "You must complete all three steps."
    ),
    tools=[save_analysis_to_state, bigquery_toolset],
)

policy_agent = Agent(
    name="Maintenance_Policy_Agent",
    model=model_name,
    description="Evaluates anomaly severity and determines required maintenance action.",
    instruction=(
        "You evaluate telemetry and dictate maintenance policy. "
        "Read 'severity' and 'diagnostic' from the session state. "
        "If severity is 'High', decide on 'EMERGENCY SHUTDOWN AND INSPECTION REQUIRED'. "
        "If severity is 'Low', decide on 'Routine Monitoring'. "
        "Call `save_decision_to_state` with your exact decision string. "
        "Do not ask the user for input."
    ),
    tools=[save_decision_to_state], # Pure logic, no external MCP tool needed here
)

alert_agent = Agent(
    name="Alert_Strategy_Agent",
    model=model_name,
    description="Finalizes the workflow and produces a dispatch summary.",
    instruction=(
        "You are the final dispatcher. "
        "Call `build_alert_summary` to retrieve the final report. "
        "Then, format this summary into a clean, professional dispatch message for the engineering team."
    ),
    tools=[build_alert_summary],
)

# --- Coordinator ---
primary_coordinator = SequentialAgent(
    name="Autonomous_Foreman_Coordinator",
    description="Runs detect -> evaluate policy -> alert in sequence.",
    sub_agents=[anomaly_agent, policy_agent, alert_agent],
)

# --- Root Agent ---
root_agent = Agent(
    name="predictive_maintenance_root",
    model=model_name,
    description="Entry point for the Predictive Maintenance system.",
    instruction=(
        "You are the Autonomous Foreman. "
        "When the user asks to check a station, delegate to the Autonomous_Foreman_Coordinator. "
        "Wait for the coordinator to finish, then present the final dispatch summary directly to the user."
    ),
    sub_agents=[primary_coordinator],
)

# --- Local test runner ---
if __name__ == "__main__":
    async def main():
        print("\n🚀 Starting local agent test")
        
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="maintenance_app",
            user_id="local_test",
        )

        runner = Runner(
            agent=root_agent,
            app_name="maintenance_app",
            session_service=session_service,
        )

        # Using a valid NOAA station ID
        user_prompt = "Run a health check on station 722020"
        print(f"User: {user_prompt}\n")

        content = types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)]
        )

        async for event in runner.run_async(
            user_id="local_test",
            session_id=session.id,
            new_message=content,
        ):
            if event.is_final_response():
                print("✅ Agent response:")
                print(event.content.parts[0].text)

    asyncio.run(main())