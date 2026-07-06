import sys
import json
from datetime import datetime
import os

# Path to the alert dispatch log file in the project directory
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "alerts_dispatch.log")

def log_alert_to_file(cluster_id, lat, lon, count, severity, details):
    """Appends the alert escalation record to the dispatch log file."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "event": "MCP_ALERT_DISPATCHED",
        "timestamp": timestamp,
        "cluster_id": cluster_id,
        "latitude": lat,
        "longitude": lon,
        "report_count": count,
        "severity": severity,
        "details": details
    }
    # Ensure logs folder or root exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    """Reads JSON-RPC messages from standard input and responds on standard output."""
    sys.stderr.write("[MCP Server] Initialized. Awaiting JSON-RPC requests via stdio...\n")
    sys.stderr.flush()

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        
        # Strip trailing newlines or whitespaces
        line = line.strip()
        if not line:
            continue
            
        try:
            req = json.loads(line)
            method = req.get("method")
            msg_id = req.get("id")
            
            # MCP Stdio Initialization Handshake
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "JalRakshakEscalationServer",
                            "version": "1.0.0"
                        }
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
                
            elif method == "notifications/initialized":
                # Notification doesn't expect a response
                continue
                
            # List Tools Endpoint
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [
                            {
                                "name": "send_alert",
                                "description": "Escalates a confirmed water contamination cluster to local health/sanitation authorities.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "cluster_id": {"type": "integer"},
                                        "latitude": {"type": "number"},
                                        "longitude": {"type": "number"},
                                        "report_count": {"type": "integer"},
                                        "severity": {"type": "string"},
                                        "details": {"type": "string"}
                                    },
                                    "required": ["cluster_id", "latitude", "longitude", "report_count", "severity"]
                                }
                            }
                        ]
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
                
            # Call Tool Endpoint
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                if tool_name == "send_alert":
                    cluster_id = args.get("cluster_id")
                    lat = args.get("latitude")
                    lon = args.get("longitude")
                    count = args.get("report_count")
                    severity = args.get("severity")
                    details = args.get("details", "")
                    
                    # Store alert into the local log file
                    log_alert_to_file(cluster_id, lat, lon, count, severity, details)
                    
                    text_msg = (
                        f"🚨 [MCP SYSTEM ALERT] Water contamination cluster ID {cluster_id} "
                        f"at ({lat:.4f}, {lon:.4f}) with {count} reports has been ESCALATED. "
                        f"Severity: {severity}. Sanitation action team dispatched."
                    )
                    
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": text_msg
                                }
                            ],
                            "isError": False
                        }
                    }
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
                else:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found."
                        }
                    }
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            else:
                # Unsupported method
                if msg_id is not None:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method '{method}' not found."
                        }
                    }
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"[MCP Server] Error processing request line: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
