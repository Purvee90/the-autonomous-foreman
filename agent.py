import os
import logging
import google.cloud.logging
from dotenv import load_dotenv

from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

from tools import get_calendar_mcp_toolset, get_bigquery_mcp_toolset

# --- Setup ---
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()
load_dotenv()

model_name = os.getenv("MODEL", "gemini-2.0-flash")


calendar_toolset = get_calendar_mcp_toolset()
bigquery_toolset = get_bigquery_mcp_toolset()



def analyze_telemetry_data(tool_context: ToolContext, machine_id: str) -> dict:
    """
    Queries BigQuery for machine telemetry.
    Compares real-time readings to historical baseline (Z-score logic).
    Saves severity + anomaly details into shared ADK state.
    """
    # TODO: Replace stub with real BigQuery MCP call
    # e.g., result = bigquery_toolset.run_query(f"SELECT ... WHERE machine_id='{machine_id}'")
    severity = "High"  # Replace with calculated value from BQ result

    # Persist findings so downstream agents can read them
    tool_context.state["machine_id"] = machine_id
    tool_context.state["severity"] = severity
    tool_context.state["anomaly_details"] = "Vibration exceeded 3-sigma baseline."

    return {"status": "success", "machine_id": machine_id, "severity": severity}


def evaluate_maintenance_window(tool_context: ToolContext) -> dict:
    """
    Reads severity from state.
    Queries Google Calendar MCP for technician availability and blackout windows.
    Saves the maintenance decision + assigned tech into shared ADK state.
    """
    severity = tool_context.state.get("severity", "Low")

    # TODO: Replace stub with real Calendar MCP call
    # e.g., slots = calendar_toolset.list_events(...)
    if severity == "High":
        decision = "Immediate Override"
        tech = "Jane Doe (On-Call)"
    else:
        decision = "Scheduled for next Tuesday at 2 AM"
        tech = "Maintenance Pool"

    tool_context.state["maintenance_decision"] = decision
    tool_context.state["assigned_tech"] = tech

    return {"status": "success", "decision": decision, "tech": tech}


def dispatch_alerts(tool_context: ToolContext) -> dict:
    """
    Reads severity, decision, and tech from state.
    Dispatches Slack/Jira alerts via MCP based on severity level.
    """
    severity = tool_context.state.get("severity", "Low")
    decision = tool_context.state.get("maintenance_decision", "Unknown")
    tech     = tool_context.state.get("assigned_tech", "Unknown")

    # TODO: Replace stub with real Slack/Jira MCP call
    # e.g., if severity == "High": slack_toolset.post_message(channel=tech, text=decision)

    return {"status": "success", "action": f"Alerted {tech} via Slack for: {decision}"}


anomaly_agent = Agent(
    name="Anomaly_Detection_Agent",
    model=model_name,
    description="Detects machine anomalies by querying telemetry data from BigQuery.",
    instruction=(
        "You are an industrial diagnostics AI. "
        "When given a machine_id, call `analyze_telemetry_data` to pull telemetry, "
        "calculate severity, and save the report to state. "
        "Do not proceed without calling the tool."
    ),
    tools=[analyze_telemetry_data, bigquery_toolset],
)

policy_agent = Agent(
    name="Maintenance_Policy_Agent",
    model=model_name,
    description="Resolves scheduling by cross-referencing severity with technician calendars.",
    instruction=(
        "You are a maintenance scheduling AI. "
        "Read the 'severity' already saved in state. "
        "Call `evaluate_maintenance_window` to check the calendar and save the decision. "
        "Do not ask the user for input — use what is in state."
    ),
    tools=[evaluate_maintenance_window, calendar_toolset],
)

alert_agent = Agent(
    name="Alert_Strategy_Agent",
    model=model_name,
    description="Dispatches work tickets and notifications based on the maintenance decision.",
    instruction=(
        "You are an alert dispatcher. "
        "Read severity, maintenance_decision, and assigned_tech from state. "
        "Call `dispatch_alerts` to send Slack/Jira notifications. "
        "Summarize what action was taken."
    ),
    tools=[dispatch_alerts],
)


# --- Sequential Coordinator ---

primary_coordinator = SequentialAgent(
    name="Autonomous_Maintenance_Coordinator",
    description="Runs the full predictive maintenance pipeline: detect → schedule → alert.",
    sub_agents=[anomaly_agent, policy_agent, alert_agent],
)


# --- Root Agent (Entry Point) ---

root_agent = Agent(
    name="predictive_maintenance_root",
    model=model_name,
    description="Entry point for the Predictive Maintenance system.",
    instruction=(
        "You are the entry point for a predictive maintenance system. "
        "When the user provides a machine_id or reports an issue, "
        "delegate immediately to the Autonomous_Maintenance_Coordinator sub-agent "
        "to run the full diagnostic and alert pipeline. "
        "Do not attempt to answer questions yourself — always delegate."
    ),
    sub_agents=[primary_coordinator],
)