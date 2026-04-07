from mcp.server.fastmcp import FastMCP
import os
import json
from datetime import datetime, timedelta

# Initialize the MCP Server
mcp = FastMCP("Calendar_Maintenance_MCP")

@mcp.tool()
def check_calendar_schedule(severity: str, station_id: str, diagnostic: str) -> str:
    """
    Checks technician availability and schedules maintenance 
    based on the severity and location of the wind turbine anomaly.
    """
    
    # In a real app, you'd use os.getenv("GOOGLE_CALENDAR_KEY") here.
    # For the hackathon, we are mocking a highly realistic scheduling engine.
    
    # 1. Determine the timeline based on severity
    now = datetime.now()
    if severity == "High":
        decision = "Immediate Emergency Override"
        scheduled_time = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    else:
        decision = "Scheduled for next optimal low-wind window"
        scheduled_time = (now + timedelta(days=2)).strftime("%Y-%m-%d 08:00:00")
        
    # 2. Determine the technician based on location (station_id)
    # (Just a simple mock dictionary mapping regions to teams)
    tech_roster = {
        "722530": "Texas Wind Team Alpha (On-Call)",
        "724940": "California Coastal Crew",
        "default": "National Response Team"
    }
    assigned_tech = tech_roster.get(station_id, tech_roster["default"])
        
    return json.dumps({
        "assigned_tech": assigned_tech, 
        "decision": decision,
        "scheduled_time": scheduled_time,
        "calendar_event_title": f"[{severity} Severity] Turbine Maintenance at Station {station_id}",
        "calendar_event_details": diagnostic
    })

if __name__ == "__main__":
    mcp.run()