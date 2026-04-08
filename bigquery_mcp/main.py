# import os
# import json
# from mcp.server.fastmcp import FastMCP
# from google.cloud import bigquery

# # Initialize FastMCP
# mcp = FastMCP("Wind_Anomaly_Detection_MCP")

# @mcp.tool()
# def analyze_wind_telemetry(station_id: str) -> str:
#     """
#     Queries NOAA ISD public dataset to detect wind speed anomalies.
#     """
#     client = bigquery.Client()
    
#     query = """
#         WITH WindData AS (
#             SELECT 
#                 stn AS station_id,
#                 TIMESTAMP(CONCAT(year, '-', mo, '-', da, ' ', hr, ':', min, ':00')) AS reading_time,
#                 CAST(wdsp AS FLOAT64) AS wind_speed_knots
#             FROM `bigquery-public-data.noaa_isd.isd_2023`
#             WHERE stn = @station_id AND wdsp != '999.9'
#         ),
#         RollingAverages AS (
#             SELECT
#                 station_id, reading_time, wind_speed_knots,
#                 AVG(wind_speed_knots) OVER(
#                     PARTITION BY station_id ORDER BY reading_time 
#                     ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
#                 ) AS rolling_avg_24h
#             FROM WindData
#         )
#         SELECT * FROM RollingAverages ORDER BY reading_time DESC LIMIT 1
#     """
    
#     job_config = bigquery.QueryJobConfig(
#         query_parameters=[bigquery.ScalarQueryParameter("station_id", "STRING", station_id)]
#     )

#     try:
#         results = list(client.query(query, job_config=job_config).result())
#         if not results:
#             return json.dumps({"status": "error", "message": f"No data for {station_id}"})
        
#         row = results[0]
#         # Logic: Anomaly if current > 2x historical average
#         baseline = row.rolling_avg_24h if row.rolling_avg_24h else 0.1
#         is_anomaly = row.wind_speed_knots > (baseline * 2.0)
        
#         return json.dumps({
#             "station_id": row.station_id,
#             "timestamp": str(row.reading_time),
#             "severity": "High" if is_anomaly else "Low",
#             "current_wind_speed": round(row.wind_speed_knots, 2),
#             "historical_baseline": round(baseline, 2),
#             "diagnostic": "Sudden wind shear detected." if is_anomaly else "Normal parameters."
#         })
#     except Exception as e:
#         return json.dumps({"status": "error", "message": str(e)})

# if __name__ == "__main__":
#     # Get port from environment (Cloud Run requirement)
#     port = int(os.environ.get("PORT", 8080))
#     # sse is the most compatible transport for web-based MCP
#     mcp.run(transport="sse", host="0.0.0.0", port=port)

import os
import json
from mcp.server.fastmcp import FastMCP
from google.cloud import bigquery

# Initialize FastMCP
mcp = FastMCP("Wind_Anomaly_Detection_MCP")

@mcp.tool()
def analyze_wind_telemetry(station_id: str) -> str:
    """Queries NOAA ISD public dataset to detect wind speed anomalies."""
    client = bigquery.Client()
    
    query = """
        WITH WindData AS (
            SELECT 
                stn AS station_id,
                TIMESTAMP(CONCAT(year, '-', mo, '-', da, ' ', hr, ':', min, ':00')) AS reading_time,
                CAST(wdsp AS FLOAT64) AS wind_speed_knots
            FROM `bigquery-public-data.noaa_isd.isd_2023`
            WHERE stn = @station_id AND wdsp != '999.9'
        ),
        RollingAverages AS (
            SELECT
                station_id, reading_time, wind_speed_knots,
                AVG(wind_speed_knots) OVER(
                    PARTITION BY station_id ORDER BY reading_time 
                    ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
                ) AS rolling_avg_24h
            FROM WindData
        )
        SELECT * FROM RollingAverages ORDER BY reading_time DESC LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("station_id", "STRING", station_id)]
    )

    try:
        results = list(client.query(query, job_config=job_config).result())
        if not results:
            return json.dumps({"status": "error", "message": f"No data for station {station_id}"})
        
        row = results[0]
        baseline = row.rolling_avg_24h if row.rolling_avg_24h else 0.1
        is_anomaly = row.wind_speed_knots > (baseline * 2.0)
        
        return json.dumps({
            "station_id": row.station_id,
            "timestamp": str(row.reading_time),
            "severity": "High" if is_anomaly else "Low",
            "current_wind_speed": round(row.wind_speed_knots, 2),
            "historical_baseline": round(baseline, 2),
            "diagnostic": "Sudden wind shear detected." if is_anomaly else "Normal parameters."
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    mcp.run(transport="sse")