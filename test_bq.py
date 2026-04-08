import os
import json
import google.auth.transport.requests
import google.oauth2.id_token

# --- UPDATED IMPORTS FOR ADK v1.28.1 ---
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

# --- 1. CONFIGURATION ---
# Replace this with your actual Cloud Run URL for the BigQuery MCP
BIGQUERY_MCP_URL = "https://bigquery-mcp-server-468548325207.europe-west1.run.app" 

print(f"🔌 Connecting to Cloud Run: {BIGQUERY_MCP_URL}")

# --- 2. AUTHENTICATION ---
try:
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, BIGQUERY_MCP_URL)
    print("✅ Successfully generated Cloud Run ID Token.")
except Exception as e:
    print("❌ Failed to get ID Token.")
    print(str(e))
    exit(1)

# --- 3. TOOLSET SETUP ---
try:
    # Notice the capital 'Mcp' instead of 'MCP'
    toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_URL,
            headers={"Authorization": f"Bearer {id_token}"}
        )
    )
    print("✅ MCP Toolset initialized.")
except Exception as e:
    print("❌ Failed to initialize toolset.")
    print(str(e))
    exit(1)

# --- 4. EXECUTE THE TOOL ---
import asyncio

async def test_tool():
    print("\n🚀 Firing 'analyze_wind_telemetry' for station 722530...")
    try:
        # Note: MCP Toolsets often require an async context in the newer ADK versions
        response = await toolset.call_tool("analyze_wind_telemetry", {"station_id": "722530"})
        print("\n🎉 SUCCESS! Raw Response:")
        print(response)
    except Exception as e:
        print("\n❌ Tool Call Failed!")
        print(str(e))

asyncio.run(test_tool())