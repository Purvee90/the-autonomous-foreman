import os
from dotenv import load_dotenv


load_dotenv() 
os.environ.pop("GEMINI_API_KEY", None) 
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = "the-autonomous-foreman"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
# ==========================================

import google.cloud.logging
from google.adk.agents import Agent, SequentialAgent
from .tools import (
    analyze_telemetry_data,
    route_technician,
    evaluate_maintenance_window,
    dispatch_alerts,
    resolve_anomaly
)

# --- Setup Logging ---
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

model_name = os.getenv("MODEL", "gemini-2.5-flash")

# ==========================================
# AGENT DEFINITIONS
# ==========================================

anomaly_agent = Agent(
    name="Watchdog_Agent",
    model=model_name,
    description="Detects machine anomalies.",
    instruction="Call `analyze_telemetry_data` to check the machine's BigQuery status.",
    tools=[analyze_telemetry_data],
)

router_agent = Agent(
    name="Location_Router_Agent",
    model=model_name,
    description="Finds the right technician.",
    instruction="Call `route_technician` to assign a technician.",
    tools=[route_technician],
)

scheduler_agent = Agent(
    name="Maintenance_Scheduler_Agent",
    model=model_name,
    description="Checks the calendar for scheduling.",
    instruction="Call `evaluate_maintenance_window` to schedule the repair.",
    tools=[evaluate_maintenance_window],
)

dispatcher_agent = Agent(
    name="Alert_Dispatcher_Agent",
    model=model_name,
    description="Sends out the tickets.",
    instruction="Call `dispatch_alerts` to notify the technician.",
    tools=[dispatch_alerts],
)

resolution_agent = Agent(
    name="Resolution_Simulator_Agent",
    model=model_name,
    description="Simulates the repair.",
    instruction="Call `resolve_anomaly` to update BigQuery and close the loop.",
    tools=[resolve_anomaly],
)


primary_coordinator = SequentialAgent(
    name="Autonomous_Maintenance_Coordinator",
    description="Runs the full predictive maintenance pipeline.",
    sub_agents=[anomaly_agent, router_agent, scheduler_agent, dispatcher_agent, resolution_agent],
)

root_agent = Agent(
    name="foreman_root",
    model=model_name,
    description="Entry point for the system.",
    instruction="""
    You are the Autonomous Foreman. 
    When the user provides a machine_id or reports an issue, delegate immediately to the Autonomous_Maintenance_Coordinator.
    If the user doesn't provide a machine ID, ask them for one.
    """,
    sub_agents=[primary_coordinator],
)
