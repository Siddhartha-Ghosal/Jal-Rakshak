import sys
import os
import shutil
from datetime import datetime
from PIL import Image

def safe_print(*args, **kwargs):
    enc = sys.stdout.encoding or 'utf-8'
    new_args = []
    for arg in args:
        if isinstance(arg, str):
            new_args.append(arg.encode(enc, errors='replace').decode(enc))
        else:
            new_args.append(arg)
    import builtins
    builtins.print(*new_args, **kwargs)

print = safe_print

# Add Capstone root to Python path so we can import backend packages
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend import database
from backend.agents import vision_agent, advisory_agent, escalation_agent

# Simple terminal text colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_banner():
    print(f"{CYAN}{BOLD}")
    print("==================================================")
    print("      JAL RAKSHAK (WATER MONITORING SKILL)        ")
    print("==================================================")
    print(f"{RESET}")

def print_help():
    print(f"Usage: python cli.py report <image_path> <latitude> <longitude>")
    print(f"Example: python cli.py report backend/static/sample.jpg 12.9716 77.5946")

def run_report(image_path: str, lat_str: str, lon_str: str):
    # Initialize DB
    database.init_db()
    
    # 1. Input Sanitization & Validation
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except ValueError:
        print(f"{RED}[Error] Latitude and longitude must be valid float numbers.{RESET}")
        sys.exit(1)
        
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        print(f"{RED}[Error] Coordinate values out of range: Lat must be in [-90, 90], Lon in [-180, 180].{RESET}")
        sys.exit(1)
        
    # File Checks
    if not os.path.exists(image_path):
        print(f"{RED}[Error] Image path '{image_path}' does not exist.{RESET}")
        sys.exit(1)
        
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    _, file_ext = os.path.splitext(image_path.lower())
    if file_ext not in allowed_extensions:
        print(f"{RED}[Error] Invalid file extension. Allowed: {', '.join(allowed_extensions)}{RESET}")
        sys.exit(1)
        
    # File size limits (5MB)
    file_size = os.path.getsize(image_path)
    if file_size > 5 * 1024 * 1024:
        print(f"{RED}[Error] Image size exceeds the 5MB security limit.{RESET}")
        sys.exit(1)
        
    # Image header validation
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as e:
        print(f"{RED}[Error] Image verification failed. File is corrupt or invalid. (Detail: {e}){RESET}")
        sys.exit(1)

    print(f"{GREEN}[OK] Inputs and Image successfully validated (Security Checks Passed).{RESET}\n")

    # Copy image to uploads folder to mock server upload behavior
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    dest_filename = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(image_path)}"
    dest_path = os.path.join(uploads_dir, dest_filename)
    
    try:
        shutil.copy2(image_path, dest_path)
        relative_url = f"/uploads/{dest_filename}"
    except Exception as e:
        print(f"{RED}[Error] Failed to copy image to uploads directory: {e}{RESET}")
        sys.exit(1)

    # 2. Pipeline Execution
    print(f"{BOLD}[1/4] Running Vision/Diagnosis Agent...{RESET}")
    diagnosis = vision_agent.diagnose_water_source(dest_path)
    signs = diagnosis["contamination_signs"]
    risk = diagnosis["risk_level"]
    confidence = diagnosis["confidence"]
    details = diagnosis["details"]
    
    risk_color = GREEN if risk == "Low" else (YELLOW if risk == "Medium" else RED)
    print(f"      - Diagnosis Mode: {diagnosis['mode']}")
    print(f"      - Contamination Signs: {signs if signs else 'None'}")
    print(f"      - Determined Risk: {risk_color}{risk}{RESET} (Confidence: {confidence:.2f})")
    print(f"      - Visual Analysis: {details}\n")

    print(f"{BOLD}[2/4] Running Advisory Agent...{RESET}")
    advisories = advisory_agent.generate_advisory(signs, risk)
    
    # Strip HTML tags for clean terminal printing
    import re
    def clean_html(raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext
        
    print(f"      - {BOLD}Safety Advice (English):{RESET}")
    print(f"        {clean_html(advisories['advisory_en'])}")
    print(f"      - {BOLD}Safety Advice (Hindi):{RESET}")
    print(f"        {clean_html(advisories['advisory_hi'])}\n")

    print(f"{BOLD}[3/4] Registering Report in Database...{RESET}")
    report_id = database.add_report(
        latitude=lat,
        longitude=lon,
        image_path=relative_url,
        contamination_signs=signs,
        risk_level=risk,
        advisory=advisories["advisory_en"] + " || " + advisories["advisory_hi"]
    )
    print(f"      {GREEN}[OK] Saved report with ID: {report_id}{RESET}\n")

    print(f"{BOLD}[4/4] Running Escalation Agent...{RESET}")
    escalation = escalation_agent.check_and_escalate_clusters(report_id)
    
    if escalation["status"] == "escalated":
        print(f"      {RED}[🚨 ALERT TRIGGERED]{RESET} Cluster detected!")
        print(f"      - Associated Reports in Cluster: {escalation['report_count']}")
        print(f"      - Cluster Coordinates: ({escalation['latitude']:.4f}, {escalation['longitude']:.4f})")
        print(f"      - {BOLD}MCP Dispatch Message:{RESET}")
        print(f"        {GREEN}{escalation['mcp_message']}{RESET}")
    elif escalation["status"] == "skipped":
        print(f"      {GREEN}[i] No escalation trigger.{RESET} Status: {escalation['message']}")
    else:
        print(f"      {RED}[Error] Escalation failed: {escalation.get('message')}{RESET}")

    print(f"\n{GREEN}==============================================")
    print("       Jal Rakshak Pipeline Complete          ")
    print(f"=============================================={RESET}")

def main():
    print_banner()
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    if cmd == "report":
        if len(sys.argv) < 5:
            print(f"{RED}[Error] Missing arguments for report command.{RESET}")
            print_help()
            sys.exit(1)
        run_report(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"{RED}[Error] Unknown command '{cmd}'{RESET}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
