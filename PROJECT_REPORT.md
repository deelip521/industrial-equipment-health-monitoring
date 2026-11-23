# Final Project Report: Industrial Equipment Health Monitoring System
**Course:** Cloud Computing & IoT Analytics  
**Assignment Number:** Assignment #23  
**Application Domain:** Smart Manufacturing & Industrial IoT (IIoT)  
**Students / Authors:** Rakshith C & Deelip  
**Date:** November 2026  

---

## Executive Summary
In modern industrial manufacturing facilities, unexpected equipment breakdown causes severe production downtime, safety hazards, and exorbitant maintenance costs. This project implements a comprehensive, cloud-hosted **Industrial Equipment Health Monitoring System** driven by real-time IoT sensor telemetry and **Predictive Maintenance Analytics**. 

The system continuously acquires and evaluates multi-variate telemetry streams—including **Temperature**, **Vibration Level**, **Pressure**, and **Power Consumption**—from industrial machinery across the shop floor. By applying weighted anomaly detection, multi-variate degradation scoring, and rule-based threshold filters, the platform calculates an instantaneous **Equipment Health Score (0-100%)**, estimates **Remaining Useful Life (RUL)** in hours, and triggers automated maintenance notifications when critical conditions arise (such as **Temperature > 80°C** or **Vibration > 5.0 mm/s**). An intuitive, dark-themed industrial SCADA dashboard delivers live time-series visualization, historical analytics, and automated daily engineering shift reports.

---

## 1. Introduction
### 1.1 Problem Statement
Traditional industrial maintenance regimes rely on either reactive maintenance (repairing equipment only after it fails) or rigid calendar-based preventative maintenance (inspecting parts regardless of their actual operational wear). Both approaches are inefficient:
- **Reactive Maintenance** results in catastrophic equipment breakdown, costly emergency repairs, and unplanned assembly line halts.
- **Calendar-Based Maintenance** frequently replaces components with significant remaining life or misses early degradation signals between maintenance intervals.

Industrial equipment like CNC milling centers, gas turbines, hydraulic pumps, and centrifugal compressors exhibit clear physical precursors prior to functional failure, primarily in the form of abnormal vibration harmonics, thermal buildup, and pressure deviations.

### 1.2 Objectives
The primary objectives of this project are:
1. **IoT Sensor Ingestion:** Deploy a resilient ingestion mechanism capable of ingesting high-frequency industrial telemetry (Temperature, Vibration, Pressure, Power, Timestamp) across multiple machines.
2. **Time-Series Persistence:** Store incoming readings in an indexed, optimized time-series database supporting high-throughput writes and rapid historical rollups.
3. **Predictive Maintenance Analytics:** Develop analytical models to compute:
   - Rolling average machine temperature
   - Vibration trendlines (detecting early bearing wear)
   - Integrated energy consumption trends (kWh)
   - Equipment operational utilisation percentages
4. **Automated Alerting Engine:** Implement real-time threshold monitoring that flags safety violations:
   - **Rule 1:** Temperature > 80°C (Overheating hazard)
   - **Rule 2:** Vibration > Threshold (5.0 mm/s ISO limit for rotary equipment)
5. **Interactive Visualization Dashboard:** Build a Grafana-styled SCADA dashboard with live multi-axis charts, equipment health dials, alert logs, and 1-click printable shift reports.

---

## 2. Cloud Resources & Architecture Design

### 2.1 Cloud Resource Stack
- **Virtual Machine (VM):** Hosted on cloud infrastructure (AWS EC2 / Azure VM / Google Compute Engine), running Ubuntu Linux. Acts as the central web server, API host, and processing engine.
- **IoT Core / IoT Hub:** Simulated and integrated message broker supporting secure edge MQTT/HTTPS communication.
- **Time-Series Database:** Optimized time-series storage schema with B-Tree indices on `(machine_id, timestamp)`, enabling sub-millisecond range queries and rollups.
- **Monitoring & Visualization:** Modern web-based SCADA interface inspired by Grafana and Rockwell Automation dashboards, utilizing Chart.js and HTML5 WebSockets.

### 2.2 System Architecture Diagram
```
+-------------------------------------------------------------------------+
|                  Industrial Shop Floor (Edge Layer)                     |
|  [CNC Milling: CNC-M01]               [Gas Turbine: TURBINE-02]         |
|  [Hydraulic Pump: PUMP-A103]          [Centrifugal Compressor-04]       |
|                                                                         |
|  Sensors: Temperature (°C) | Vibration (mm/s) | Pressure | Power (kW)   |
+------------------------------------+------------------------------------+
                                     |
                         IoT Telemetry Stream (JSON)
                                     v
+-------------------------------------------------------------------------+
|                Cloud Virtual Machine (AWS EC2 / Azure VM)               |
|                                                                         |
|  +----------------------------+      +-------------------------------+  |
|  | IoT Streaming & Simulator  | ---> | Predictive Analytics Engine   |  |
|  | - Telemetry Ingestion Hub  |      | - Health Score (0-100%)       |  |
|  | - Fault Injection Controls |      | - Remaining Useful Life (RUL) |  |
|  +----------------------------+      | - Failure Risk Probability    |  |
|                |                     +-------------------------------+  |
|                v                                     |                  |
|  +----------------------------+                      v                  |
|  | Time-Series Database       |      +-------------------------------+  |
|  | - sensor_telemetry (Index) | <--- | Rule-Based Alerting Engine    |  |
|  | - maintenance_alerts       |      | - Temp > 80°C | Vib > 5 mm/s  |  |
|  +----------------------------+      +-------------------------------+  |
|                |                                     |                  |
|                +------------------+------------------+                  |
|                                   |                                     |
|                                   v                                     |
|  +-------------------------------------------------------------------+  |
|  | Web Application Server (FastAPI / ASGI / WebSocket Broker)        |  |
|  +-------------------------------------------------------------------+  |
+-----------------------------------+-------------------------------------+
                                    | Real-Time WebSockets & HTTP
                                    v
+-------------------------------------------------------------------------+
|                     Visualization & Operations Layer                    |
|  - Real-Time SCADA Grafana-Styled Dashboard                             |
|  - Dual-Axis Telemetry Charts (Temp & Vibration)                        |
|  - Equipment Health Score Gauge & RUL Predictor                         |
|  - Live Maintenance Alerts Table with Ack/Clear                         |
|  - Automated Daily Equipment Shift & Health Report (Printable)          |
+-------------------------------------------------------------------------+
```

### 2.3 IoT Data Pipeline
1. **Generation:** Sensors attached to each industrial asset sample temperature, vibration velocity, line pressure, and active electrical draw at 2-second intervals.
2. **Ingestion:** Telemetry payloads are packaged as JSON dictionaries with ISO timestamps and transmitted to the ingestion API endpoint.
3. **Database Write:** Every reading is appended to the `sensor_telemetry` table.
4. **Analytical Inference:** The analytics module runs the payload through health degradation algorithms and failure probability functions.
5. **Rule Evaluation:** If temperature exceeds 80°C or vibration exceeds 5.0 mm/s, an alert record is logged in the `maintenance_alerts` table.
6. **Live Broadcast:** Telemetry batches are broadcast over WebSocket connections to all connected web clients in sub-second latency.

---

## 3. Database Design & Telemetry Schema

### 3.1 Entity Relationship & Table Structures
The time-series database is engineered around three structured tables:

#### 1. `equipment` (Master Metadata Table)
Stores machine asset information and baseline operating parameters:
- `machine_id` (VARCHAR PK): e.g., `CNC-M01`
- `name` (VARCHAR): Descriptive equipment title
- `type` (VARCHAR): Machine category (e.g., Milling, Turbine, Pump)
- `location` (VARCHAR): Bay / Shop floor designation
- `nominal_temp` (REAL): Baseline temperature under normal load (°C)
- `nominal_vibration` (REAL): Baseline vibration velocity (mm/s)
- `nominal_pressure` (REAL): Baseline pressure (bar)
- `nominal_power` (REAL): Baseline power consumption (kW)

#### 2. `sensor_telemetry` (Time-Series Data Table)
Stores time-indexed raw operational data:
- `id` (INTEGER PK AUTOINCREMENT)
- `machine_id` (TEXT NOT NULL, Indexed)
- `timestamp` (TEXT NOT NULL, Indexed)
- `temperature` (REAL NOT NULL)
- `vibration` (REAL NOT NULL)
- `pressure` (REAL NOT NULL)
- `power` (REAL NOT NULL)
- `status` (TEXT NOT NULL)

*Indexing Strategy:* Composite index created on `(machine_id, timestamp)` to ensure range scans over time windows execute in $O(\log N)$ time.

#### 3. `maintenance_alerts` (Incident & Alert Table)
Maintains full audit trails for equipment safety violations:
- `id` (INTEGER PK AUTOINCREMENT)
- `machine_id` (TEXT NOT NULL)
- `timestamp` (TEXT NOT NULL)
- `severity` (TEXT NOT NULL) — `WARNING` or `CRITICAL`
- `rule_triggered` (TEXT NOT NULL) — e.g., `RULE-01: HIGH_TEMPERATURE`
- `metric_name` (TEXT NOT NULL)
- `metric_value` (REAL NOT NULL)
- `threshold_value` (REAL NOT NULL)
- `message` (TEXT NOT NULL)
- `status` (TEXT NOT NULL) — `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`

---

## 4. Implementation Details

### 4.1 Backend Architecture
The backend is developed using Python 3.14 and **FastAPI**, an asynchronous web framework built on ASGI standard:
- **`app.py`**: Coordinates HTTP routes, WebSocket lifecycle, and JSON responses.
- **`database.py`**: Encapsulates SQLite queries, connection pooling, and aggregation functions.
- **`analytics.py`**: Contains the mathematical logic for multi-variate health scoring, anomaly evaluation, and RUL estimation.
- **`simulator.py`**: Multi-threaded IoT generator that runs background cycles to emulate realistic shop-floor telemetry and handle on-demand fault injections.

### 4.2 Predictive Health Score Formulation
The equipment health score $H(t) \in [0, 100]$ is computed as a weighted penalty function from nominal baseline deviations:

$$H(t) = \max\left(5.0, 100.0 - (P_{\text{temp}} + P_{\text{vib}} + P_{\text{press}} + P_{\text{power}})\right)$$

Where:
- **Thermal Penalty ($P_{\text{temp}}$, 35% weight):**
  $$P_{\text{temp}} = 35 \times \min\left(1.0, \frac{T - 80.0}{20.0} + 0.6\right) \quad \text{for } T > 80.0^\circ\text{C}$$
- **Vibration Penalty ($P_{\text{vib}}$, 40% weight):**
  $$P_{\text{vib}} = 40 \times \min\left(1.0, \frac{V - 5.0}{4.0} + 0.6\right) \quad \text{for } V > 5.0\text{ mm/s}$$
- **Pressure Penalty ($P_{\text{press}}$, 15% weight):** Evaluates deviation from nominal pressure limits.
- **Power Penalty ($P_{\text{power}}$, 10% weight):** Penalizes electrical surge $>130\%$ of rated capacity.

### 4.3 Remaining Useful Life (RUL) & Failure Risk
- **Failure Risk:** Calculated using a logistic sigmoid model mapping the health score $H$:
  $$\text{Risk}(\%) = \frac{100}{1 + e^{-\frac{70 - H}{12}}}$$
- **Remaining Useful Life (RUL):** Extrapolates running hours before mechanical failure. Healthy assets maintain $2000-2800$ operating hours, while critical degradation drops RUL to $<48$ hours.

### 4.4 Alert Rules Implementation
1. **Rule 1 (High Temperature):** Triggers when $T > 80.0^\circ\text{C}$. Severity is classified as `WARNING` ($80^\circ\text{C}-92^\circ\text{C}$) or `CRITICAL` ($>92^\circ\text{C}$).
2. **Rule 2 (Excessive Vibration):** Triggers when $V > 5.0\text{ mm/s}$ (conforming to ISO 10816 Class III/IV rotary machinery vibration guidelines).

---

## 5. Testing & Experimental Results

### 5.1 Test Cases & Functional Verification
| Test Case | Scenario / Input | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| **TC-01** | Start application and connect dashboard | Machine chips populate; WebSocket connects; live charts plot telemetry | All 4 machines loaded; WebSocket connected; charts plot every 2s | **PASS** |
| **TC-02** | Inject Overheat Fault ($T > 80^\circ\text{C}$) | Temperature rises above 80°C; `RULE-01` triggers; alert logged in table; card flashes | Temp reached 87.2°C; Warning logged; alert appeared instantly | **PASS** |
| **TC-03** | Inject Vibration Spike ($V > 5.0\text{ mm/s}$) | Vibration rises $>5.0$; `RULE-02` triggers; Health score drops $<60\%$ | Vibration peaked at 7.1 mm/s; Health score fell to 48%; Alert logged | **PASS** |
| **TC-04** | Acknowledge Alert | Alert row updates from `ACTIVE` to `ACKNOWLEDGED` | Alert status persisted and button disabled | **PASS** |
| **TC-05** | Daily Report Generation | `/report/{machine_id}` renders printable summary with all KPIs and shift audit | Comprehensive report rendered with zero styling errors | **PASS** |
| **TC-06** | Cloud Telemetry Ingestion API | `POST /api/telemetry/ingest` with custom payload | Reading stored in DB; health evaluated; response code 200 | **PASS** |

### 5.2 Performance Analytics Evaluation
- **Average Temperature Calculation:** Verified across 1,000 continuous readings with dynamic SQL aggregations.
- **Vibration Trend Analysis:** Monitored first-derivative regression slope; successfully tagged trends as `STABLE (Normal)`, `INCREASING (Deterioration)`, or `DECREASING`.
- **Energy Consumption:** Integrated power draw over time:
  $$E = \sum P(t) \times \Delta t \text{ (in kWh)}$$
- **Equipment Utilisation:** Accurately calculated percentage breakdown across `Active`, `Warning`, and `Downtime` states.

---

## 6. Demonstration Walkthrough Guide (3-5 Minutes)

When demonstrating the project during evaluation:
1. **Step 1: System Overview (Minute 1):**
   - Open `http://localhost:8000` in the browser.
   - Explain the header banner displaying **Rakshith C & Deelip (Assignment 23)** and the green "IoT Core Stream: Connected" indicator.
   - Highlight the 4 industrial assets: `CNC-M01`, `TURBINE-02`, `PUMP-A103`, and `COMPRESSOR-04`.
2. **Step 2: Live Telemetry & Dual Charts (Minute 2):**
   - Show the real-time line charts dynamically scrolling every 2 seconds.
   - Explain Chart 1 (Temperature in red & Vibration in blue) and Chart 2 (Pressure in green & Power in yellow).
   - Point out the Health Score gauge displaying 98% with "Optimal mechanical condition."
3. **Step 3: Alert Rules Demonstration (Minute 3):**
   - Click the red button: **"🔥 Simulate Overheating (>80°C)"**.
   - Observe the temperature card flashing red as it exceeds 80°C.
   - Show the Live Alerts table immediately logging `RULE-01: HIGH_TEMPERATURE`.
   - Click the red button: **"📳 Inject Vibration Spike (>5.0 mm/s)"**.
   - Observe vibration exceeding 5.0 mm/s, health score dropping to ~45%, and `RULE-02: EXCESSIVE_VIBRATION` appearing in the alert table.
   - Click the "Acknowledge" button on the alert row.
4. **Step 4: Shift Analytics & Daily Report (Minute 4-5):**
   - Point to the Analytics row: Average Temperature, Vibration Trend (`INCREASING`), Energy Consumed (kWh), and Utilisation %.
   - Click the top-right button: **"📄 Generate Daily Report"**.
   - Display the formal, printable **Daily Equipment Health & Predictive Maintenance Report**, showing management-ready diagnostics and prescriptive maintenance recommendations.

---

## 7. Conclusion & Future Enhancements

### 7.1 Conclusion
The Industrial Equipment Health Monitoring System successfully fulfills all specifications outlined in Assignment #23. By combining cloud-grade time-series data storage, live streaming protocols, and domain-informed predictive maintenance analytics, the system transforms raw industrial telemetry into actionable operational insights. Both mandatory alert rules (Temperature > 80°C and Vibration > 5.0 mm/s) function reliably, protecting mechanical assets from sudden breakdown.

### 7.2 Lessons Learned
- Implementing efficient indexing on compound keys `(machine_id, timestamp)` is vital for keeping high-frequency sensor dashboards responsive.
- Real-time WebSockets offer substantial latency improvements over traditional HTTP polling for time-critical industrial alarms.
- Weighted multi-sensor health scoring provides significantly earlier warning than isolated single-parameter thresholds.

### 7.3 Future Enhancements
- Integration with edge hardware (e.g., Raspberry Pi or ESP32 with physical accelerometer and thermal thermocouples).
- Advanced Deep Learning models (LSTM / Transformer autoencoders) for unsupervised vibration anomaly detection.
- Automated generation of CMMS (Computerized Maintenance Management System) work orders via cloud webhook triggers.
