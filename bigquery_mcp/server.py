from mcp.server.fastmcp import FastMCP

mcp = FastMCP("BigQuery_Telemetry_Server")

@mcp.tool()
def get_telemetry(machine_id: str) -> str:
    """Queries BigQuery for telemetry."""
    # Real GCP code goes here!
    return f"Data for {machine_id}: ANOMALY"

if __name__ == "__main__":
    mcp.run()
