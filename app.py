"""
Main Application Server
FastAPI Web Application for Industrial Equipment Health Monitoring System
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from datetime import datetime

from database import (
    init_db,
    get_all_machines,
    get_recent_telemetry,
    get_active_alerts,
    acknowledge_alert,
    clear_alerts,
    get_equipment_analytics,
    insert_telemetry,
    insert_alert
)
from analytics import compute_equipment_health, evaluate_alert_rules
from simulator import streaming_engine

app = FastAPI(
    title="Industrial Equipment Health Monitoring System",
    description="Predictive Maintenance Analytics for Industrial IoT Equipment",
    version="1.0.0"
)

# Mount static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Connected WebSocket clients
connected_websockets: List[WebSocket] = []
main_loop: Optional[asyncio.AbstractEventLoop] = None
latest_live_cache: Dict[str, Any] = {}

def ws_broadcast_adapter(batch_data: Dict[str, Any]):
    """Called by the background simulator thread to broadcast data to all web clients."""
    global main_loop, latest_live_cache
    latest_live_cache = batch_data
    if main_loop and main_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(broadcast_to_clients(batch_data), main_loop)
        except Exception as e:
            print("[Broadcast Error]", e)

async def broadcast_to_clients(data: Dict[str, Any]):
    disconnected = []
    for ws in list(connected_websockets):
        try:
            await ws.send_json({"type": "TELEMETRY_UPDATE", "data": data})
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in connected_websockets:
            connected_websockets.remove(ws)

@app.on_event("startup")
async def on_startup():
    global main_loop
    main_loop = asyncio.get_running_loop()
    init_db()
    streaming_engine.initialize()
    streaming_engine.broadcast_callback = ws_broadcast_adapter
    streaming_engine.start()
    print("Application initialized successfully with active asyncio loop.")

@app.on_event("shutdown")
def on_shutdown():
    streaming_engine.stop()

# --- Web UI Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Industrial Equipment Monitoring Dashboard Loading...</h1>")

@app.get("/report/{machine_id}", response_class=HTMLResponse)
async def generate_daily_report(machine_id: str):
    """Generates the printable Daily Equipment Health & Predictive Maintenance Report."""
    machines = {m["machine_id"]: m for m in get_all_machines()}
    if machine_id not in machines:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    machine = machines[machine_id]
    analytics = get_equipment_analytics(machine_id)
    recent = get_recent_telemetry(machine_id, limit=30)
    alerts = [a for a in get_active_alerts(50) if a["machine_id"] == machine_id]
    
    last_reading = recent[-1] if recent else {
        "temperature": machine["nominal_temp"],
        "vibration": machine["nominal_vib"],
        "pressure": machine["nominal_pressure"],
        "power": machine["nominal_power"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    health = compute_equipment_health(
        last_reading["temperature"],
        last_reading["vibration"],
        last_reading["pressure"],
        last_reading["power"],
        machine["nominal_temp"],
        machine["nominal_vib"],
        machine["nominal_pressure"],
        machine["nominal_power"]
    )

    alert_rows_html = "".join([
        f"""<tr>
            <td>{a['timestamp']}</td>
            <td><span class="badge {a['severity'].lower()}">{a['severity']}</span></td>
            <td>{a['rule_triggered']}</td>
            <td>{a['metric_name']}: {a['metric_value']} (Limit: {a['threshold_value']})</td>
            <td>{a['message']}</td>
        </tr>""" for a in alerts[:10]
    ]) if alerts else "<tr><td colspan='5' style='text-align:center;'>No alerts recorded during this reporting period. Machine in healthy state.</td></tr>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Daily Equipment Health Report - {machine_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #fff; color: #222; }}
        .header {{ border-bottom: 3px solid #1a365d; padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: flex-end; }}
        h1 {{ margin: 0; color: #1a365d; font-size: 24px; }}
        .meta {{ font-size: 13px; color: #555; }}
        .section-title {{ font-size: 16px; font-weight: bold; background: #edf2f7; padding: 8px 12px; margin-top: 25px; margin-bottom: 15px; border-left: 4px solid #2b6cb0; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .card {{ background: #f7fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; }}
        .card .title {{ font-size: 12px; color: #718096; text-transform: uppercase; font-weight: 600; }}
        .card .value {{ font-size: 22px; font-weight: bold; color: #2d3748; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }}
        th {{ background: #edf2f7; font-weight: 600; }}
        .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .badge.critical {{ background: #fed7d7; color: #9b2c2c; }}
        .badge.warning {{ background: #feebc8; color: #9c4221; }}
        .badge.normal {{ background: #c6f6d5; color: #22543d; }}
        .print-btn {{ background: #2b6cb0; color: white; border: none; padding: 10px 18px; border-radius: 4px; cursor: pointer; font-size: 14px; }}
        @media print {{ .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 20px; text-align: right;">
        <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>
    </div>
    <div class="header">
        <div>
            <h1>Industrial Equipment Health & Predictive Maintenance Report</h1>
            <div class="meta">Facility: Smart Manufacturing Plant #1 | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 20px; font-weight: bold; color: #2b6cb0;">{machine['machine_id']}</div>
            <div style="font-size: 13px; color: #4a5568;">{machine['name']} ({machine['type']})</div>
        </div>
    </div>

    <div class="section-title">1. Equipment Health & Diagnostic Summary</div>
    <div class="grid">
        <div class="card">
            <div class="title">Health Index</div>
            <div class="value" style="color: {'#38a169' if health['health_score'] > 75 else ('#d69e2e' if health['health_score'] > 50 else '#e53e3e')}">{health['health_score']}%</div>
            <div style="font-size: 12px; color: #718096; margin-top: 4px;">Status: <b>{health['status']}</b></div>
        </div>
        <div class="card">
            <div class="title">Failure Risk (48h)</div>
            <div class="value">{health['failure_risk_pct']}%</div>
            <div style="font-size: 12px; color: #718096; margin-top: 4px;">Mode: {health['failure_mode']}</div>
        </div>
        <div class="card">
            <div class="title">Est. Remaining Useful Life</div>
            <div class="value">{health['rul_hours']} hrs</div>
            <div style="font-size: 12px; color: #718096; margin-top: 4px;">Before critical overhaul</div>
        </div>
        <div class="card">
            <div class="title">Active Utilisation</div>
            <div class="value">{analytics['utilisation']['active_percent']}%</div>
            <div style="font-size: 12px; color: #718096; margin-top: 4px;">Downtime: {analytics['utilisation']['downtime_percent']}%</div>
        </div>
    </div>

    <div style="background: #ebf8ff; border: 1px solid #bee3f8; padding: 12px; border-radius: 6px; font-size: 13px; margin-bottom: 20px;">
        <b>Engineering Diagnostic:</b> {health['diagnostic']}<br/>
        <b>Prescriptive Maintenance Action:</b> {health['recommendation']}
    </div>

    <div class="section-title">2. Operational Sensor Analytics</div>
    <table>
        <tr>
            <th>Telemetry Parameter</th>
            <th>Current Value</th>
            <th>Operational Average</th>
            <th>Nominal Baseline</th>
            <th>Threshold Limit</th>
            <th>Assessment</th>
        </tr>
        <tr>
            <td>Temperature (°C)</td>
            <td><b>{last_reading['temperature']}°C</b></td>
            <td>{analytics['avg_temperature']}°C (Max: {analytics['max_temperature']}°C)</td>
            <td>{machine['nominal_temp']}°C</td>
            <td>80.0°C</td>
            <td><span class="badge {'critical' if last_reading['temperature'] > 80 else 'normal'}">{'ALERT (>80°C)' if last_reading['temperature'] > 80 else 'Normal'}</span></td>
        </tr>
        <tr>
            <td>Vibration Velocity (mm/s)</td>
            <td><b>{last_reading['vibration']} mm/s</b></td>
            <td>{analytics['avg_vibration']} mm/s (Trend: {analytics['vibration_trend']})</td>
            <td>{machine['nominal_vib']} mm/s</td>
            <td>5.0 mm/s</td>
            <td><span class="badge {'critical' if last_reading['vibration'] > 5.0 else 'normal'}">{'ALERT (>5.0 mm/s)' if last_reading['vibration'] > 5.0 else 'Normal'}</span></td>
        </tr>
        <tr>
            <td>Pressure (bar)</td>
            <td><b>{last_reading['pressure']} bar</b></td>
            <td>Nominal: {machine['nominal_pressure']} bar</td>
            <td>{machine['nominal_pressure']} bar</td>
            <td>2.0 - 9.0 bar</td>
            <td><span class="badge {'warning' if last_reading['pressure'] < 2.0 or last_reading['pressure'] > 9.0 else 'normal'}">{'Deviating' if last_reading['pressure'] < 2.0 or last_reading['pressure'] > 9.0 else 'Normal'}</span></td>
        </tr>
        <tr>
            <td>Power Draw (kW)</td>
            <td><b>{last_reading['power']} kW</b></td>
            <td>Avg: {analytics['avg_power_kw']} kW</td>
            <td>{machine['nominal_power']} kW</td>
            <td>{machine['nominal_power'] * 1.4:.1f} kW</td>
            <td><span class="badge normal">Normal Draw</span></td>
        </tr>
        <tr>
            <td>Cumulative Energy Consumed</td>
            <td colspan="5"><b>{analytics['energy_consumed_kwh']} kWh</b> across {analytics['total_readings']} telemetry samples recorded.</td>
        </tr>
    </table>

    <div class="section-title">3. Recent Incident & Alert History</div>
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Severity</th>
                <th>Rule Name</th>
                <th>Metric Detail</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            {alert_rows_html}
        </tbody>
    </table>

    <div style="margin-top: 35px; border-top: 1px solid #ccc; padding-top: 15px; font-size: 11px; color: #888; text-align: center;">
        Cloud IoT Predictive Maintenance Platform | Confidential Engineering Report
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

# --- REST API Endpoints ---

@app.get("/api/machines")
def get_machines_api():
    return get_all_machines()

@app.get("/api/telemetry/recent")
def get_telemetry_api(machine_id: str, limit: int = 60):
    return get_recent_telemetry(machine_id, limit)

@app.get("/api/telemetry/live")
def get_live_telemetry_batch():
    """Returns the latest live telemetry batch for all machines."""
    return latest_live_cache

@app.get("/api/analytics/{machine_id}")
def get_analytics_api(machine_id: str):
    return get_equipment_analytics(machine_id)

@app.get("/api/alerts")
def get_alerts_api(limit: int = 50):
    return get_active_alerts(limit)

@app.post("/api/alerts/{alert_id}/acknowledge")
def ack_alert_api(alert_id: int):
    acknowledge_alert(alert_id)
    return {"status": "success", "alert_id": alert_id}

@app.post("/api/alerts/clear")
def clear_alerts_api():
    clear_alerts()
    return {"status": "success"}

class SimulatorModeRequest(BaseModel):
    machine_id: str
    mode: str
    duration: Optional[int] = 40

@app.post("/api/simulator/mode")
def set_simulator_mode_api(req: SimulatorModeRequest):
    success = streaming_engine.set_machine_mode(req.machine_id, req.mode, req.duration)
    if not success:
        raise HTTPException(status_code=404, detail="Machine ID not found in simulator")
    return {"status": "success", "machine_id": req.machine_id, "mode": req.mode}

class ExternalTelemetryIngest(BaseModel):
    machine_id: str
    temperature: float
    vibration: float
    pressure: float
    power: float
    timestamp: Optional[str] = None

@app.post("/api/telemetry/ingest")
def ingest_external_telemetry(data: ExternalTelemetryIngest):
    """External Cloud Ingestion endpoint (e.g. from AWS IoT Core / Azure IoT Hub)."""
    ts = data.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    machines = {m["machine_id"]: m for m in get_all_machines()}
    mach = machines.get(data.machine_id, {
        "nominal_temp": 55.0, "nominal_vib": 1.8, "nominal_pressure": 5.0, "nominal_power": 20.0
    })

    health = compute_equipment_health(
        data.temperature, data.vibration, data.pressure, data.power,
        mach.get("nominal_temp", 55.0), mach.get("nominal_vib", 1.8),
        mach.get("nominal_pressure", 5.0), mach.get("nominal_power", 20.0)
    )

    item = {
        "machine_id": data.machine_id,
        "timestamp": ts,
        "temperature": data.temperature,
        "vibration": data.vibration,
        "pressure": data.pressure,
        "power": data.power,
        "status": health["status"]
    }
    insert_telemetry(item)

    alerts = evaluate_alert_rules(
        data.machine_id, ts, data.temperature, data.vibration, data.pressure, data.power
    )
    for a in alerts:
        insert_alert(a)

    return {"status": "ingested", "health": health, "alerts_triggered": len(alerts)}

# --- WebSocket Telemetry Stream ---

@app.websocket("/ws/stream")
async def websocket_telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        while True:
            # Keep connection alive & handle incoming client commands if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
    except Exception:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
