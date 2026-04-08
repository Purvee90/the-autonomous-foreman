# import os
# import google.auth
# import google.auth.transport.requests
# from google.adk.tools.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams
# from dotenv import load_dotenv

# load_dotenv()

# BIGQUERY_MCP_URL = os.getenv('BIGQUERY_MCP_URL')
# CALENDAR_MCP_URL = os.getenv('CALENDAR_MCP_URL')

# def get_calendar_mcp_toolset():
#     return MCPToolset(
#         connection_params=StreamableHTTPConnectionParams(
#             url=CALENDAR_MCP_URL
#         )
#     )

# def get_bigquery_mcp_toolset():
#     # credentials, project_id = google.auth.default(
#     #     scopes=["https://www.googleapis.com/auth/bigquery"]
#     # )
#     # credentials.refresh(google.auth.transport.requests.Request())
#     auth_req = google.auth.transport.requests.Request()
#     id_token = google.oauth2.id_token.fetch_id_token(auth_req, BIGQUERY_MCP_URL)
#     return MCPToolset(
#         connection_params=StreamableHTTPConnectionParams(
#             url=BIGQUERY_MCP_URL,
#             headers={
#                 "Authorization": f"Bearer {credentials.token}",
#                 "x-goog-user-project": project_id
#             }
#         )
#     )

import os
import google.auth.transport.requests
import google.oauth2.id_token
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from dotenv import load_dotenv

load_dotenv()

# The ADK will inject this URL after it hoists the server
BIGQUERY_MCP_URL = os.getenv('BIGQUERY_MCP_URL', 'http://localhost:8080')
SSE_ENDPOINT = f"{BIGQUERY_MCP_URL}/sse"

def get_bigquery_mcp_toolset():
    headers = {}
    
    # Attempt to fetch OIDC token for secure ADK deployments
    try:
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, BIGQUERY_MCP_URL)
        headers["Authorization"] = f"Bearer {id_token}"
    except Exception:
        pass # ADK likely deployed it without requiring auth

    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=SSE_ENDPOINT,
            headers=headers
        )
    )