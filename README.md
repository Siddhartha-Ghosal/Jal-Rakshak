# 💧 Jal Rakshak (जल रक्षक)
### AI-Powered Multi-Agent Water Safety & Contamination Monitoring System

> **An intelligent multi-agent platform that empowers communities to detect, report, analyze, and escalate water contamination using AI, computer vision, and the Model Context Protocol (MCP).**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue.svg)
![MCP](https://img.shields.io/badge/MCP-Enabled-orange.svg)
![Gemini](https://img.shields.io/badge/Gemini-Optional-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

# 🌍 Overview

**Jal Rakshak** is a **local-first AI-powered water monitoring system** built to help rural and semi-urban communities identify potentially contaminated water sources before they become public health hazards.

Instead of relying solely on manual inspections, citizens simply upload a photograph of a pond, well, river, or community tap along with its GPS location.

The system automatically performs:

- 🔍 Water quality analysis
- 🤖 AI-based contamination assessment
- 🌐 Dual-language safety advisories (English + Hindi)
- 📍 Geographic clustering of incidents
- 🚨 Automatic authority alerts through the Model Context Protocol (MCP)

The project demonstrates how multiple AI agents can collaborate to solve a real societal problem while remaining lightweight, explainable, and capable of running entirely offline.

---

# 🎯 Problem Statement

Across many communities, contaminated water sources often remain unreported until numerous people become ill.

Current reporting methods suffer from:

- Slow manual verification
- Lack of technical expertise
- Poor communication
- Delayed authority response
- No centralized incident tracking

**Jal Rakshak** addresses these challenges by providing an intelligent, automated reporting and escalation system powered by AI agents.

---

# ✨ Key Features

- 📸 Image-based contamination reporting
- 🤖 Multi-Agent AI Architecture
- 🌍 GPS-based incident tracking
- 🧠 Vision analysis using Pillow (Offline) or Gemini Vision (Optional)
- 📢 Automatic bilingual advisories
- 📍 Spatial clustering using Haversine Distance
- 🚨 MCP-based authority notification
- 💾 SQLite database
- 🌐 FastAPI web dashboard
- 💻 Command-line Agent Skill (CLI)
- 🔒 Secure image validation
- ⚡ Fully local execution without cloud dependency

---

# 🏗 System Architecture

```text
                 Citizen

                   │
                   │
     Upload Image + GPS Coordinates
                   │
                   ▼
        FastAPI Backend Server
                   │
                   ▼
     ┌───────────────────────────┐
     │ Vision Diagnosis Agent    │
     │                           │
     │ • Image Analysis          │
     │ • Risk Detection          │
     │ • Water Classification    │
     └───────────────────────────┘
                   │
                   ▼
     ┌───────────────────────────┐
     │ Advisory Agent            │
     │                           │
     │ • English Guidance        │
     │ • Hindi Guidance          │
     │ • Safety Recommendations  │
     └───────────────────────────┘
                   │
                   ▼
     ┌───────────────────────────┐
     │ Escalation Agent          │
     │                           │
     │ • Database Storage        │
     │ • Cluster Detection       │
     │ • Haversine Distance      │
     └───────────────────────────┘
                   │
      3 Nearby Reports within
        2 km & 48 Hours?
                   │
          Yes ─────────────► MCP Client
                              │
                              ▼
                     MCP Server
                              │
                              ▼
                    send_alert Tool
                              │
                              ▼
                 Authority Notification
```

---

# 🤖 Multi-Agent Workflow

## 1️⃣ Vision Agent

The Vision Agent performs image analysis to identify visual indicators of contaminated water.

It detects:

- Green algae growth
- Turbid or muddy water
- Foam accumulation
- Water discoloration
- Overall contamination risk

The system supports two operating modes:

### Offline Mode

Uses **Pillow** to calculate average RGB values and classify contamination through explainable heuristics.

### Online Mode

Uses **Google Gemini Vision** for richer scene understanding when an API key is available.

---

## 2️⃣ Advisory Agent

Based on the contamination level identified by the Vision Agent, this agent generates clear and practical public safety guidance.

It produces:

- English advisory
- Hindi advisory
- Risk explanation
- Recommended precautions

This ensures accessibility for multilingual communities.

---

## 3️⃣ Escalation Agent

Every report is stored in the SQLite database.

The Escalation Agent continuously checks for nearby contamination reports.

If **three or more reports** occur:

- within **2 km**
- within **48 hours**

the system automatically escalates the incident.

Spatial calculations are performed using the **Haversine Formula**, providing accurate great-circle distance measurements.

---

## 4️⃣ MCP Server

Instead of directly calling a notification function, Jal Rakshak demonstrates real **Model Context Protocol (MCP)** communication.

The MCP implementation includes:

- initialize handshake
- initialized event
- tools/list
- tools/call
- JSON-RPC communication
- stdio transport

When a contamination cluster is detected, the Escalation Agent invokes the **send_alert** tool through the MCP Client.

This simulates notifying local authorities in a protocol-compliant manner.

---

# 🛠 Technology Stack

| Category | Technologies |
|-----------|--------------|
| Backend | FastAPI |
| Programming | Python |
| Database | SQLite |
| Vision | Pillow |
| AI | Google Gemini (Optional) |
| Protocol | Model Context Protocol (MCP) |
| API | REST |
| CLI | Python |
| Image Processing | PIL |
| Environment | python-dotenv |

---

# 📂 Project Structure

```text
Jal-Rakshak/
│
├── backend/
│   ├── agents/
│   │   ├── vision_agent.py
│   │   ├── advisory_agent.py
│   │   └── escalation_agent.py
│   │
│   ├── database.py
│   ├── main.py
│   ├── mcp_client.py
│   ├── mcp_server.py
│   └── uploads/
│
├── frontend/
│
├── cli.py
├── requirements.txt
├── README.md
└── .env.example
```

---

# 🔒 Security Features

The project follows several security best practices:

- Image extension whitelist
- Maximum upload size validation
- Pillow image verification
- Latitude validation
- Longitude validation
- Parameterized SQL queries
- No personal information stored
- Local-first architecture

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/Jal-Rakshak.git

cd Jal-Rakshak
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment (Optional)

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

If omitted, the project automatically switches to Offline Vision Mode.

---

# ▶ Running the Application

## Start FastAPI

```bash
python -m uvicorn backend.main:app --reload
```

Visit:

```
http://localhost:8000
```

---

## Run CLI Agent

```bash
python cli.py report image.jpg 12.9716 77.5946
```

---

# 🧪 Example Workflow

1. Upload an image
2. Enter latitude and longitude
3. Vision Agent analyzes contamination
4. Advisory Agent generates bilingual safety advice
5. Database stores report
6. Escalation Agent checks nearby reports
7. If a contamination cluster exists:
   - MCP Client connects
   - MCP Server executes `send_alert`
   - Authority notification is logged

---

# 🎯 Real-World Applications

- Rural water monitoring
- Panchayat administration
- Disaster response
- Public health surveillance
- Smart villages
- Environmental protection
- NGO field operations
- Citizen science initiatives

---

# 🔮 Future Improvements

- Mobile application
- Satellite imagery support
- IoT water sensors
- AI segmentation models
- Government dashboard
- SMS notifications
- WhatsApp integration
- Live GIS mapping
- Historical analytics
- Predictive contamination forecasting

---

# 🤝 Contributing

Contributions are welcome!

Feel free to:

- Fork the repository
- Create a feature branch
- Commit your improvements
- Open a Pull Request

---

# 📜 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

**Siddhartha Ghosal**  
**Amrita Chakraborty**

B.Tech CSE (AI & ML)

Passionate about building AI systems that solve real-world societal challenges through intelligent agents, computer vision, and automation.

---

# ⭐ If you found this project useful...

Please consider giving the repository a **Star ⭐** to support the project.
