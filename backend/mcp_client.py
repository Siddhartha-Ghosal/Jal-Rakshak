import subprocess
import json
import sys
import os

def call_mcp_send_alert(cluster_id: int, latitude: float, longitude: float, report_count: int, severity: str, details: str) -> dict:
    """
    Connects to the local MCP server via stdio, handshakes, and executes the `send_alert` tool.
    Returns the result dict from the MCP server.
    """
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")
    
    # Use sys.executable to run the server with the exact same Python binary
    proc = subprocess.Popen(
        [sys.executable, "-u", server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    def send_message(msg):
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        
    def read_message():
        line = proc.stdout.readline()
        if not line:
            return None
        return json.loads(line.strip())

    try:
        # Step 1: initialize handshake
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "JalRakshakClient", "version": "1.0.0"}
            }
        }
        send_message(init_req)
        init_resp = read_message()
        if not init_resp or "error" in init_resp:
            raise RuntimeError(f"MCP Init failed: {init_resp}")
            
        # Step 2: initialized notification
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        send_message(init_notif)
        
        # Step 3: tools/call send_alert
        call_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "send_alert",
                "arguments": {
                    "cluster_id": int(cluster_id),
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "report_count": int(report_count),
                    "severity": str(severity),
                    "details": str(details)
                }
            }
        }
        send_message(call_req)
        call_resp = read_message()
        
        # Clean shutdown of the server
        proc.terminate()
        proc.wait(timeout=2)
        
        if not call_resp:
            return {"status": "error", "message": "No response received from MCP server tool call."}
            
        if "error" in call_resp:
            return {"status": "error", "message": call_resp["error"].get("message")}
            
        return {
            "status": "success",
            "response": call_resp.get("result", {})
        }
        
    except Exception as e:
        proc.kill()
        return {
            "status": "error",
            "message": f"MCP Client connection error: {str(e)}"
        }
