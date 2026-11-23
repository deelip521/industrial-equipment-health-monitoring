# Industrial Equipment Health Monitoring System
### Predictive Maintenance Analytics for Industrial IoT Equipment
**Course Assignment:** Assignment #23 - Manufacturing Domain  
**Authors:** Rakshith C & Deelip  

---

## 📌 Project Overview
This project is an end-to-end cloud-ready **Industrial IoT Predictive Maintenance Application** built to continuously monitor machine health, analyze sensor streams, compute failure risk metrics, evaluate safety alert rules, and generate operational shift reports.

### 🏭 Monitored Industrial Equipment
1. **CNC-M01**: 5-Axis CNC Milling Center (Shop Floor Bay A)
2. **TURBINE-02**: Gas Turbine Generator Gen-2 (Power Plant Unit 1)
3. **PUMP-A103**: High-Pressure Hydraulic Pump (Press Section Bay B)
4. **COMPRESSOR-04**: Centrifugal Air Compressor 4 (Utility Plant Room)

---

## 🚀 Key Features

1. **Continuous IoT Sensor Streaming:**
   - Samples **Temperature (°C)**, **Vibration (mm/s)**, **Pressure (bar)**, and **Power Consumption (kW)** every 2 seconds.
   - Built-in multi-asset background simulator with on-demand fault injection.

2. **Predictive Maintenance Analytics:**
   - **Equipment Health Score (0-100%):** Multi-variate weighted degradation index based on ISO 10816 standards.
   - **Remaining Useful Life (RUL):** Operating hours remaining before catastrophic overhaul.
   - **Failure Risk Probability (%):** Logistic failure prediction model.
   - **Failure Mode Diagnostics:** Identifies root causes (e.g., Bearing Wear, Thermal Overload, Seal Leakage).

3. **Performance Metrics & Analytics:**
   - Rolling Average Machine Temperature (°C).
   - Vibration Trend Indicator (Stable vs Deteriorating).
   - Integrated Energy Consumption (kWh).
   - Equipment Utilisation Percentage (Active, Warning, Downtime).

4. **Alert Rules Engine:**
   - 🚨 **Rule 1:** `Temperature > 80.0 °C`
   - 🚨 **Rule 2:** `Vibration > 5.0 mm/s` (ISO threshold for heavy rotary machinery)
   - ⚠️ **Rule 3:** Hydraulic Pressure Anomaly (`< 2.0` or `> 9.0 bar`)
   - Interactive alarm acknowledgment and resolution log.

5. **Visual SCADA / Grafana-Styled Dashboard:**
   - Dark theme industrial web dashboard with real-time Chart.js dual-axis telemetry charts.
   - Health score gauge with dynamic color shifting (Green $\rightarrow$ Yellow $\rightarrow$ Red).
   - Real-time WebSocket streaming.

6. **Daily Equipment Health & Shift Report:**
   - 1-click printable and exportable engineering report (`/report/{machine_id}`).

---

## 🛠️ Project Structure
```
industrial-equipment-health-monitor/
├── app.py                 # FastAPI Web & WebSocket application
├── database.py            # SQLite time-series storage & analytics queries
├── analytics.py           # Predictive maintenance scoring, RUL & alert rules
├── simulator.py           # Multi-asset IoT telemetry generator & fault injector
├── static/
│   ├── css/
│   │   └── dashboard.css  # Dark industrial UI styling (Grafana-inspired)
│   ├── js/
│   │   └── app.js         # Real-time WebSocket/charting logic
│   └── index.html         # Live dashboard interface
├── requirements.txt       # Python package dependencies
├── run.bat                # 1-Click launcher script for Windows
├── test_app.py            # Verification and test suite script
├── ARCHITECTURE.md        # Solution architecture & IoT data pipeline diagrams
├── PROJECT_REPORT.md      # Comprehensive 5-8 page project report
└── README.md              # Project documentation
```

---

## ⚡ How to Run

### Option 1: Quick Launch (Windows)
Double-click `run.bat` or run:
```cmd
run.bat
```

### Option 2: Manual Terminal Launch
1. Navigate to the project directory:
   ```powershell
   cd C:\Users\patil\.gemini\antigravity\scratch\industrial-equipment-health-monitor
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Start the application server:
   ```powershell
   python app.py
   ```
4. Open your web browser and go to:
   **[http://localhost:8000](http://localhost:8000)**

---

## 🧪 Testing Fault Injection for Demonstrations

The dashboard provides buttons in the **Live IoT Simulator Controls** bar to easily demonstrate the required features during your 3-5 minute presentation:

| Button | Simulated Condition | Observable Dashboard Effect |
|---|---|---|
| **🔥 Simulate Overheating (>80°C)** | Temperature rises to 85°C - 94°C | **RULE-01** triggers; Temperature card flashes red; Alert is added to table; Health score decreases. |
| **📳 Inject Vibration Spike (>5.0 mm/s)** | Vibration rises to 5.5 - 8.5 mm/s | **RULE-02** triggers; Vibration card flashes red; Health score drops to Critical; RUL decreases to <48h. |
| **💥 Combined Critical Failure** | High temp + high vib + pressure drop | Compound failure alert; Emergency trip recommendation displayed. |
| **🌱 Restore Normal Mode** | Returns parameters to nominal values | System stabilizes; Status returns to `NORMAL`; Health score recovers. |
| **📄 Generate Daily Report** | Opens printable shift report | Complete PDF-ready equipment diagnostic report with audit logs and metrics. |

---

## 🌐 REST API Endpoints

- `GET /api/machines`: List all monitored machines.
- `GET /api/telemetry/recent?machine_id=CNC-M01`: Fetch recent time-series data.
- `GET /api/analytics/{machine_id}`: Get calculated analytics (Avg temp, Vibration trend, Energy kWh, Utilisation).
- `GET /api/alerts`: Get list of recent alerts.
- `POST /api/alerts/{id}/acknowledge`: Acknowledge an alert.
- `POST /api/alerts/clear`: Clear all alerts.
- `POST /api/simulator/mode`: Change simulation mode (`NORMAL`, `OVERHEAT`, `VIBRATION_SPIKE`, `HIGH_LOAD`, `CRITICAL_DEGRADE`).
- `POST /api/telemetry/ingest`: Ingest external sensor telemetry.
- `GET /report/{machine_id}`: Printable daily health report.
- `WS /ws/stream`: WebSocket streaming endpoint for live telemetry.
