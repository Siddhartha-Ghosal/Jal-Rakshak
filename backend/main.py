import os
import uuid
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io

from backend import database
from backend.agents import vision_agent, advisory_agent, escalation_agent

# Initialize FastAPI
app = FastAPI(
    title="Jal Rakshak API",
    description="Full-stack multi-agent system for water source contamination detection and escalation.",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure folders exist
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize DB on Startup
@app.on_event("startup")
def startup_event():
    database.init_db()
    print("[Server] Database initialized successfully.")

# API: Report water contamination
@app.post("/api/report")
async def report_contamination(
    latitude: str = Form(...),
    longitude: str = Form(...),
    image: UploadFile = File(...)
):
    # 1. Sanitize and Validate Location Input
    try:
        lat = float(latitude)
        lon = float(longitude)
    except ValueError:
        raise HTTPException(status_code=400, detail="Latitude and Longitude must be valid numbers.")
        
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise HTTPException(status_code=400, detail="Latitude must be in [-90, 90] and Longitude in [-180, 180].")

    # 2. Security Checks: Validate Image Upload (File size and structure)
    # File format validation (extension)
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    _, file_ext = os.path.splitext(image.filename.lower())
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")

    # Read image contents into memory for size check
    contents = await image.read()
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the 5MB limit.")

    # Image header validation via PIL (prevent malicious disguised uploads)
    try:
        img_temp = Image.open(io.BytesIO(contents))
        img_temp.verify()  # Verifies the file is actually a valid image
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid or readable image.")

    # Write file to secure path
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    # If the user included matching keywords, we can preserve them in the unique name for mock diagnosis
    test_keywords = ["algae", "discoloration", "foam", "debris"]
    for kw in test_keywords:
        if kw in image.filename.lower():
            unique_filename = f"{kw}_{unique_filename}"
            
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Relative path for web serving
    relative_image_path = f"/uploads/{unique_filename}"

    try:
        # 3. Step 1: Execute Vision/Diagnosis Agent
        diagnosis = vision_agent.diagnose_water_source(file_path)
        
        # 4. Step 2: Execute Advisory Agent
        advisories = advisory_agent.generate_advisory(
            contamination_signs=diagnosis["contamination_signs"],
            risk_level=diagnosis["risk_level"]
        )

        # 5. Step 3: Write report to SQLite Database
        report_id = database.add_report(
            latitude=lat,
            longitude=lon,
            image_path=relative_image_path,
            contamination_signs=diagnosis["contamination_signs"],
            risk_level=diagnosis["risk_level"],
            advisory=advisories["advisory_en"] + " || " + advisories["advisory_hi"]
        )

        # 6. Step 4: Execute Escalation Agent (checks cluster rule & triggers MCP server if met)
        escalation = escalation_agent.check_and_escalate_clusters(report_id)

        # Build response schema
        return {
            "status": "success",
            "report_id": report_id,
            "coordinates": {"latitude": lat, "longitude": lon},
            "image_url": relative_image_path,
            "diagnosis": {
                "contamination_signs": diagnosis["contamination_signs"],
                "risk_level": diagnosis["risk_level"],
                "confidence": diagnosis["confidence"],
                "details": diagnosis["details"],
                "mode": diagnosis["mode"]
            },
            "advisory": {
                "en": advisories["advisory_en"],
                "hi": advisories["advisory_hi"]
            },
            "escalation": escalation
        }

    except Exception as e:
        # Clean up image file on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")


# API: Fetch all reports
@app.get("/api/reports")
def get_reports():
    reports = database.get_all_reports()
    # Split bilingual advisory back into parts for the frontend
    for r in reports:
        parts = r["advisory"].split(" || ")
        r["advisory_en"] = parts[0] if len(parts) > 0 else r["advisory"]
        r["advisory_hi"] = parts[1] if len(parts) > 1 else ""
    return reports


# API: Fetch all clusters
@app.get("/api/clusters")
def get_clusters():
    return database.get_all_clusters()


# API: Fetch dispatch alerts log (MCP triggers)
@app.get("/api/alerts")
def get_alerts():
    alerts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "alerts_dispatch.log")
    if not os.path.exists(alerts_file):
        return []
        
    alerts = []
    try:
        with open(alerts_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    alerts.append(json.loads(line))
    except Exception as e:
        print(f"[Server] Error reading alerts log: {e}")
        
    # Return reverse chronological alerts
    return list(reversed(alerts))


# Serve uploads folder static assets
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Serve UI static folder at root
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {"message": "Jal Rakshak Server Running. Frontend folder not created yet."}
