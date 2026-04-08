from mcp.server.fastmcp import FastMCP
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
from datetime import datetime, timedelta

mcp = FastMCP("Calendar_Maintenance_MCP")

# The scope defines what the agent is allowed to do (read/write calendar)
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Authenticates using the Service Account JSON key."""
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

@mcp.tool()
def schedule_maintenance_event(severity: str, station_id: str, diagnostic: str) -> str:
    """
    Creates a real Google Calendar event for turbine maintenance based on severity.
    """
    service = get_calendar_service()
    now = datetime.now()
    
    # 1. Determine timeline
    if severity == "High":
        decision = "Immediate Emergency Override"
        start_time = now + timedelta(minutes=15)
        end_time = start_time + timedelta(hours=4) # 4 hour emergency block
    else:
        decision = "Scheduled for optimal low-wind window"
        start_time = now + timedelta(days=2)
        start_time = start_time.replace(hour=8, minute=0, second=0) # 8 AM two days from now
        end_time = start_time + timedelta(hours=8)
        
    # 2. Format times for Google API (RFC3339 format)
    start_str = start_time.isoformat() + 'Z'
    end_str = end_time.isoformat() + 'Z'

    # 3. Create the event body
    event_body = {
        'summary': f'[{severity} Severity] Turbine Maintenance - Station {station_id}',
        'description': f'**Diagnostic Report:**\n{diagnostic}\n\n**Action:** {decision}',
        'start': {
            'dateTime': start_str,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_str,
            'timeZone': 'UTC',
        },
        'colorId': '11' if severity == "High" else '5' # Red for high, yellow for low
    }

    try:
        # Note: We use the specific calendar ID. If you shared your primary calendar, 
        # use the email address of that calendar.
        calendar_id = 'primary' # Change this if using a dedicated testing calendar
        
        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        
        return json.dumps({
            "status": "success",
            "decision": decision,
            "event_link": event.get('htmlLink'),
            "scheduled_start": start_str
        })
        
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    mcp.run()