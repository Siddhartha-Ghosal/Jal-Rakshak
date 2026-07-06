# Jal Rakshak - End-to-End Walkthrough Guide 💧

Follow this step-by-step guide to run, test, and verify the Jal Rakshak multi-agent system and local MCP Server capabilities.

---

## Step 1: Setup and Initialize

1. **Open Workspace**:
   Ensure you are in the project folder `e:\Capstone_Project`.

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate Static Mock Images**:
   Run the image generator script to create test images inside `backend/static/`:
   ```bash
   python backend/generate_test_images.py
   ```
   This generates:
   - `backend/static/sample_algae.jpg` (a solid green image simulating algae scum)
   - `backend/static/sample_discoloration.jpg` (a solid brown image simulating mud/turbidity)
   - `backend/static/sample_clear.jpg` (a solid blue/sky-blue image simulating clean water)

---

## Step 2: Verify CLI Agent Skill (Headless Mode)

You can run reports directly in your terminal to verify each agent stage works as designed:

1. **Submit an Algae Report**:
   ```bash
   python cli.py report backend/static/sample_algae.jpg 12.9716 77.5946
   ```
   **Expected CLI Output Trace**:
   - `[✓] Inputs and Image successfully validated (Security Checks Passed).`
   - `[1/4] Running Vision/Diagnosis Agent...` (Logs that it analyzed average RGB colors, detected high green profile, and labeled it as 'algae').
   - `[2/4] Running Advisory Agent...` (Outputs dual-language English/Hindi advisories warning that boiling does not destroy cyanotoxins).
   - `[3/4] Registering Report in Database...` (Logs database report ID creation, e.g. `Saved report with ID: 1`).
   - `[4/4] Running Escalation Agent...` (Logs `Only 1 reports near this location. Skipping escalation`).

2. **Submit a Discolored Water Report**:
   ```bash
   python cli.py report backend/static/sample_discoloration.jpg 28.6139 77.2090
   ```
   - Checks color parameters, flags `discoloration` risk, registers the report, and writes to SQLite.

---

## Step 3: Run the Web Dashboard

1. **Launch the FastAPI Server**:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```
   *Note: This starts the web portal and automatically initializes the SQLite schema.*

2. **Open the App**:
   Navigate to **[http://localhost:8000](http://localhost:8000)** in your browser. You will see a beautiful dark, glassmorphic control dashboard.

---

## Step 4: Simulate a Contamination Cluster (MCP Tool Call)

We will submit 3 reports close to each other in Bengaluru to trigger the Escalation Agent's spatial-temporal cluster checks.

1. **Submit First Report**:
   - Click **Mock Location** in the UI to load coordinates: `12.9716`, `77.5946` (or type them in).
   - Drag and drop or browse to select `backend/static/sample_algae.jpg`.
   - Click **Submit Report**.
   - Watch the **Live Agent Pipeline Monitor** light up step-by-step.
   - Once completed, review the generated English/Hindi safety advisory in the pop-up modal. Close the modal.

2. **Submit Second Report**:
   - Click **Mock Location** to load coordinates: `12.9785`, `77.6012` (~1.0 km away).
   - Upload `backend/static/sample_discoloration.jpg`.
   - Click **Submit Report**. Close the pop-up advisory modal.

3. **Submit Third Report (Escalation Trigger)**:
   - Click **Mock Location** to load coordinates: `12.9730`, `77.5990` (~0.5 km away from Center, creating a 3-point cluster within 2.0 km).
   - Upload `backend/static/sample_algae.jpg` (or any sample).
   - Click **Submit Report**.
   - Notice the **Live Agent Pipeline Monitor** step 3 status:
     `Escalation Agent: Cluster detected! Local authorities escalated via MCP Server.`
   - In the right-hand panel, notice that:
     1. A blinking warning card appears in **MCP Authority Alerts**.
     2. The list of **Reported Water Sources** shows these reports are now marked with a red tag: `Escalated via MCP`.

---

## Step 5: Verify the MCP Server logs

Behind the scenes, when the 3rd report triggered a cluster, the backend executed `mcp_client.py`, spawned `mcp_server.py` as a local subprocess, completed the JSON-RPC initialization handshake over standard input/output streams, and executed the `send_alert` tool call.

1. **Verify the Dispatch Log File**:
   Open the file `alerts_dispatch.log` generated in your project root:
   ```json
   {"event": "MCP_ALERT_DISPATCHED", "timestamp": "2026-07-06T00:42:00.123456", "cluster_id": 1, "latitude": 12.9743, "longitude": 77.5982, "report_count": 3, "severity": "High", "details": "Water contamination cluster of 3 reports detected in a 2.0km radius. Suspected symptoms: algae, discoloration."}
   ```
   *This file is local proof of a successful tool-use escalation.*

2. **Verify Database Records**:
   You can inspect the SQLite file `jalrakshak.db` using standard CLI tools or Python:
   - Notice that the 3 clustered reports have their `cluster_id` set to `1` and `escalated` set to `1`.
