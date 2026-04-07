from mcp.server.fastmcp import FastMCP
from google.cloud import bigquery
import json

# Initialize the MCP Server
mcp = FastMCP("Wind_Anomaly_Detection_MCP")

@mcp.tool()
def analyze_wind_telemetry(station_id: str) -> str:
    """
    Queries the NOAA ISD public dataset to detect wind speed anomalies 
    for a specific weather station/turbine location.
    """
    # Cloud Run automatically handles the credentials using the default service account
    client = bigquery.Client()
    
    # We query a recent year's table (e.g., 2023) from the public dataset.
    # The query calculates the current wind speed and a 24-hour rolling average 
    # to establish a baseline for anomaly detection.
    query = f"""
        WITH WindData AS (
            SELECT 
                stn AS station_id,
                TIMESTAMP(CONCAT(year, '-', mo, '-', da, ' ', hr, ':', min, ':00')) AS reading_time,
                CAST(wdsp AS FLOAT64) AS wind_speed_knots
            FROM 
                `bigquery-public-data.noaa_isd.isd_2023`
            WHERE 
                stn = @station_id 
                AND wdsp != '999.9' -- Filter out missing/corrupted sensor data
        ),
        RollingAverages AS (
            SELECT
                station_id,
                reading_time,
                wind_speed_knots,
                AVG(wind_speed_knots) OVER(
                    PARTITION BY station_id 
                    ORDER BY reading_time 
                    -- Calculates average over the preceding 24 readings (approx 24 hours)
                    ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
                ) AS rolling_avg_24h
            FROM 
                WindData
        )
        SELECT 
            station_id,
            reading_time,
            wind_speed_knots,
            rolling_avg_24h
        FROM 
            RollingAverages
        ORDER BY 
            reading_time DESC
        LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("station_id", "STRING", station_id)]
    )
    
    try:
        results = list(client.query(query, job_config=job_config).result())
        
        if not results:
            return json.dumps({"status": "error", "message": f"No data found for station {station_id}."})
            
        row = results[0]
        
        # Anomaly Logic: If the current wind speed is double the 24-hour average, flag as High severity.
        # This represents a sudden, massive gust event that could damage turbine mechanics.
        is_anomaly = row.wind_speed_knots > (row.rolling_avg_24h * 2.0)
        severity = "High" if is_anomaly else "Low"
            
        return json.dumps({
            "station_id": row.station_id,
            "timestamp": str(row.reading_time),
            "severity": severity,
            "current_wind_speed": round(row.wind_speed_knots, 2),
            "historical_baseline": round(row.rolling_avg_24h, 2),
            "diagnostic": "Sudden wind shear detected." if is_anomaly else "Wind speeds within normal operational parameters."
        })
        
    except Exception as e:
         return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    # Runs the FastMCP server
    mcp.run()