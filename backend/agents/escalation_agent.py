import math
from datetime import datetime
from backend import database
from backend.mcp_client import call_mcp_send_alert

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on the Earth's surface
    using the Haversine formula. Returns distance in kilometers.
    """
    R = 6371.0  # Earth's radius in kilometers
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lon / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return R * c

def check_and_escalate_clusters(new_report_id: int) -> dict:
    """
    Analyzes recent unescalated reports. If 3 or more reports (including the new one)
    cluster within a 2.0 km radius and a 48-hour window, it triggers an escalation
    alert via the local MCP server.
    """
    print(f"[Escalation Agent] Checking cluster rules for Report ID: {new_report_id}...")
    
    # 1. Fetch all reports from DB to locate the newly added report details
    reports = database.get_all_reports()
    new_report = next((r for r in reports if r["id"] == new_report_id), None)
    
    if not new_report:
        return {"status": "skipped", "message": f"Report ID {new_report_id} not found."}
        
    lat1 = new_report["latitude"]
    lon1 = new_report["longitude"]
    time1 = datetime.fromisoformat(new_report["timestamp"])
    
    # 2. Get unescalated reports and filter by timeframe (48 hours)
    unescalated = database.get_unescalated_reports()
    
    # Ensure new_report itself is counted in unescalated (as it is not yet escalated or associated)
    if not any(r["id"] == new_report_id for r in unescalated):
        unescalated.append(new_report)
        
    clustered_reports = []
    
    for r in unescalated:
        # Check temporal constraint (within 48 hours)
        try:
            r_time = datetime.fromisoformat(r["timestamp"])
            time_diff_hours = abs((time1 - r_time).total_seconds()) / 3600.0
            
            if time_diff_hours <= 48.0:
                # Check spatial constraint (within 2.0 km)
                dist = haversine_distance(lat1, lon1, r["latitude"], r["longitude"])
                if dist <= 2.0:
                    clustered_reports.append(r)
        except Exception as e:
            print(f"[Escalation Agent] Error parsing time/distance for report {r.get('id')}: {e}")
            continue

    print(f"[Escalation Agent] Found {len(clustered_reports)} reports in spatial-temporal vicinity.")

    # 3. Trigger escalation if 3 or more reports cluster
    if len(clustered_reports) >= 3:
        print(f"[Escalation Agent] CLUSTER DETECTED! Size: {len(clustered_reports)}. Proceeding to escalate.")
        
        # Calculate cluster center
        lat_avg = sum(r["latitude"] for r in clustered_reports) / len(clustered_reports)
        lon_avg = sum(r["longitude"] for r in clustered_reports) / len(clustered_reports)
        
        # Determine cluster severity
        risk_levels = [r["risk_level"] for r in clustered_reports]
        if "High" in risk_levels:
            severity = "High"
        elif "Medium" in risk_levels:
            severity = "Medium"
        else:
            severity = "Low"
            
        # Collect signs
        all_signs = set()
        for r in clustered_reports:
            if r["contamination_signs"]:
                for s in r["contamination_signs"].split(","):
                    s_clean = s.strip()
                    if s_clean:
                        all_signs.add(s_clean)
                        
        signs_summary = ", ".join(all_signs) if all_signs else "No visible signs"
        details = (
            f"Water contamination cluster of {len(clustered_reports)} reports detected in a 2.0km radius. "
            f"Suspected symptoms: {signs_summary}."
        )
        
        # Save cluster to SQLite
        cluster_id = database.create_cluster(lat_avg, lon_avg, severity)
        
        # Associate reports to the new cluster
        report_ids = [r["id"] for r in clustered_reports]
        database.associate_reports_with_cluster(report_ids, cluster_id)
        
        # Call the local MCP Server via the MCP Client
        mcp_res = call_mcp_send_alert(
            cluster_id=cluster_id,
            latitude=lat_avg,
            longitude=lon_avg,
            report_count=len(clustered_reports),
            severity=severity,
            details=details
        )
        
        if mcp_res.get("status") == "success":
            # Mark these reports as escalated in the DB
            database.mark_reports_as_escalated(report_ids)
            print("[Escalation Agent] Cluster successfully escalated via MCP Tool Call.")
            return {
                "status": "escalated",
                "cluster_id": cluster_id,
                "report_count": len(clustered_reports),
                "latitude": lat_avg,
                "longitude": lon_avg,
                "mcp_message": mcp_res["response"]["content"][0]["text"]
            }
        else:
            print(f"[Escalation Agent] MCP escalation failed: {mcp_res.get('message')}")
            return {
                "status": "error",
                "message": f"MCP Escalation failed: {mcp_res.get('message')}"
            }
            
    else:
        print("[Escalation Agent] No cluster threshold met (less than 3 reports). Skipping escalation.")
        return {
            "status": "skipped",
            "message": f"Only {len(clustered_reports)} reports near this location. 3+ required for escalation."
        }
