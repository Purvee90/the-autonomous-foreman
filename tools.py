import time
from google.adk.tools.tool_context import ToolContext

# ==========================================
# 🗄️ THE CLOSED-LOOP DATABASE (Mock BigQuery)
# ==========================================
# In a real GCP deployment, these functions would use the google-cloud-bigquery library.
# For the hackathon demo, this shared dictionary acts as your live database.
HACKATHON_DB = {
    "722530": {"status": "ANOMALY", "wind_speed_mph": 45.0, "baseline": 15.0},
    "724940": {"status": "NORMAL", "wind_speed_mph": 12.0, "baseline": 12.0}
}

# --- 1. The Watchdog (READS from BigQuery) ---
def analyze_telemetry_data(tool_context: ToolContext, machine_id: str) -> dict:
    print(f"\n[🔍 Watchdog Agent] Querying BigQuery for Station {machine_id}...")
    time.sleep(1.5) 
    
    # Read the live status from our "Database"
    db_record = HACKATHON_DB.get(machine_id, {"status": "UNKNOWN"})
    severity = "High" if db_record["status"] == "ANOMALY" else "Normal"
    
    # Save the findings to the Agent's short-term memory
    tool_context.state["machine_id"] = machine_id
    tool_context.state["severity"] = severity
    
    print(f"[🚨 Watchdog Agent] DB Status is {db_record['status']}. {severity} severity anomaly detected!")
    return {"status": "success", "machine_id": machine_id, "severity": severity}

# --- 2. The Router ---
def route_technician(tool_context: ToolContext) -> dict:
    machine_id = tool_context.state.get("machine_id", "Unknown")
    print(f"\n[🗺️ Router Agent] Mapping Station {machine_id} to nearest technician...")
    time.sleep(1)
    tech = "Texas Wind Team Alpha" if machine_id == "722530" else "National Emergency Response Team"
    tool_context.state["assigned_tech"] = tech
    print(f"[✅ Router Agent] Assigned {tech}.")
    return {"status": "success", "tech": tech}

# --- 3. The Scheduler ---
def evaluate_maintenance_window(tool_context: ToolContext) -> dict:
    severity = tool_context.state.get("severity", "Low")
    tech = tool_context.state.get("assigned_tech", "Unknown")
    print(f"\n[📅 Scheduler Agent] Checking Calendar for {tech}...")
    time.sleep(1.5)
    decision = "Immediate Dispatch" if severity == "High" else "Scheduled next window"
    tool_context.state["maintenance_decision"] = decision
    print(f"[✅ Scheduler Agent] Decision: {decision}")
    return {"status": "success", "decision": decision}

# --- 4. The Dispatcher ---
def dispatch_alerts(tool_context: ToolContext) -> dict:
    decision = tool_context.state.get("maintenance_decision", "Unknown")
    tech = tool_context.state.get("assigned_tech", "Unknown")
    machine_id = tool_context.state.get("machine_id", "Unknown")
    print(f"\n[✉️ Dispatch Agent] Pinging Slack & Creating Ticket...")
    time.sleep(1)
    alert_msg = f"ALERT {tech}: Station {machine_id} requires maintenance."
    print(f"--> 📩 MESSAGE SENT: '{alert_msg}'")
    return {"status": "success", "action": alert_msg}

# --- 5. The Simulator (WRITES to BigQuery to Close the Loop) ---
def resolve_anomaly(tool_context: ToolContext) -> dict:
    machine_id = tool_context.state.get("machine_id", "Unknown")
    print(f"\n[🔧 Simulator Agent] Technician has repaired Station {machine_id}...")
    time.sleep(2)
    
    # THE CLOSED LOOP: We update the actual "database" to prove it's fixed
    if machine_id in HACKATHON_DB:
        HACKATHON_DB[machine_id]["status"] = "NORMAL"
        HACKATHON_DB[machine_id]["wind_speed_mph"] = HACKATHON_DB[machine_id]["baseline"]
    
    print(f"[✅ Simulator Agent] BigQuery updated: Station {machine_id} is now NORMAL. Loop Closed!")
    return {"status": "success", "resolution": f"Machine {machine_id} fixed and DB updated."}
