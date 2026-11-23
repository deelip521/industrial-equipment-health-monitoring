"""
Database Module for Industrial Equipment Health Monitoring System
Handles time-series storage, indexing, rollups, and alert persistence.
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import random

DB_PATH = os.path.join(os.path.dirname(__file__), "equipment_health.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Time-Series Sensor Telemetry Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        temperature REAL NOT NULL,
        vibration REAL NOT NULL,
        pressure REAL NOT NULL,
        power REAL NOT NULL,
        status TEXT NOT NULL
    )
    """)

    # Indices for high performance time-series queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_machine_time ON sensor_telemetry(machine_id, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time ON sensor_telemetry(timestamp)")

    # Equipment Master Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        machine_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        location TEXT NOT NULL,
        installation_date TEXT NOT NULL,
        nominal_temp REAL NOT NULL,
        nominal_vibration REAL NOT NULL,
        nominal_pressure REAL NOT NULL,
        nominal_power REAL NOT NULL
    )
    """)

    # Maintenance Alerts Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maintenance_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        severity TEXT NOT NULL,
        rule_triggered TEXT NOT NULL,
        metric_name TEXT NOT NULL,
        metric_value REAL NOT NULL,
        threshold_value REAL NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE'
    )
    """)

    # Pre-populate machines if empty
    cursor.execute("SELECT COUNT(*) FROM equipment")
    if cursor.fetchone()[0] == 0:
        initial_machines = [
            ("CNC-M01", "5-Axis CNC Milling Center", "CNC Machine", "Shop Floor Bay A", "2024-01-15", 55.0, 1.8, 5.0, 18.5),
            ("TURBINE-02", "Gas Turbine Generator Gen-2", "Turbine", "Power Plant Unit 1", "2023-08-10", 68.0, 2.5, 6.2, 45.0),
            ("PUMP-A103", "High-Pressure Hydraulic Pump", "Hydraulic System", "Press Section Bay B", "2024-03-22", 48.0, 1.2, 7.5, 12.0),
            ("COMPRESSOR-04", "Centrifugal Air Compressor 4", "Compressor", "Utility Plant Room", "2023-11-05", 52.0, 1.5, 5.8, 22.0)
        ]
        cursor.executemany("""
        INSERT INTO equipment (machine_id, name, type, location, installation_date, nominal_temp, nominal_vibration, nominal_pressure, nominal_power)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_machines)

    # Pre-populate historical telemetry readings if table has fewer than 20 records
    cursor.execute("SELECT COUNT(*) FROM sensor_telemetry")
    if cursor.fetchone()[0] < 20:
        cursor.execute("SELECT * FROM equipment")
        machs = [dict(r) for r in cursor.fetchall()]
        now = datetime.now()
        seed_records = []
        for offset in range(30, 0, -1):
            t_str = (now - timedelta(seconds=offset * 2)).strftime("%Y-%m-%d %H:%M:%S")
            for m in machs:
                t_val = round(m["nominal_temp"] + random.uniform(-1.0, 1.2), 2)
                v_val = round(m["nominal_vibration"] + random.uniform(-0.15, 0.18), 2)
                p_val = round(m["nominal_pressure"] + random.uniform(-0.2, 0.2), 2)
                pw_val = round(m["nominal_power"] + random.uniform(-0.5, 0.6), 2)
                seed_records.append((m["machine_id"], t_str, t_val, v_val, p_val, pw_val, "NORMAL"))
        cursor.executemany("""
        INSERT INTO sensor_telemetry (machine_id, timestamp, temperature, vibration, pressure, power, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, seed_records)

    conn.commit()
    conn.close()

def insert_telemetry(telemetry: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sensor_telemetry (machine_id, timestamp, temperature, vibration, pressure, power, status)
    VALUES (:machine_id, :timestamp, :temperature, :vibration, :pressure, :power, :status)
    """, telemetry)
    conn.commit()
    conn.close()

def insert_alert(alert: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO maintenance_alerts (machine_id, timestamp, severity, rule_triggered, metric_name, metric_value, threshold_value, message, status)
    VALUES (:machine_id, :timestamp, :severity, :rule_triggered, :metric_name, :metric_value, :threshold_value, :message, 'ACTIVE')
    """, alert)
    conn.commit()
    conn.close()

def get_recent_telemetry(machine_id: str, limit: int = 60) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM sensor_telemetry 
    WHERE machine_id = ? 
    ORDER BY timestamp DESC 
    LIMIT ?
    """, (machine_id, limit))
    rows = cursor.fetchall()
    conn.close()
    result = [dict(row) for row in rows]
    result.reverse()  # Chronological order
    return result

def get_all_machines() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipment ORDER BY machine_id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_active_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM maintenance_alerts 
    ORDER BY timestamp DESC 
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def acknowledge_alert(alert_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE maintenance_alerts SET status = 'ACKNOWLEDGED' WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()

def clear_alerts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE maintenance_alerts SET status = 'RESOLVED'")
    conn.commit()
    conn.close()

def get_equipment_analytics(machine_id: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calculate average temperature, avg vibration, max power, count
    cursor.execute("""
    SELECT 
        AVG(temperature) as avg_temp,
        MAX(temperature) as max_temp,
        MIN(temperature) as min_temp,
        AVG(vibration) as avg_vibration,
        MAX(vibration) as max_vibration,
        AVG(power) as avg_power,
        SUM(power * (1.0/3600.0)) as energy_kwh,
        COUNT(*) as total_samples
    FROM sensor_telemetry
    WHERE machine_id = ?
    """, (machine_id,))
    row = cursor.fetchone()
    
    # Vibration trend calculation (compare average of last 15 vs previous 15)
    cursor.execute("""
    SELECT vibration FROM sensor_telemetry 
    WHERE machine_id = ? 
    ORDER BY timestamp DESC 
    LIMIT 30
    """, (machine_id,))
    vib_rows = [r[0] for r in cursor.fetchall()]
    
    vib_trend = "STABLE"
    vib_slope = 0.0
    if len(vib_rows) >= 10:
        recent = sum(vib_rows[: len(vib_rows)//2]) / (len(vib_rows)//2)
        older = sum(vib_rows[len(vib_rows)//2 :]) / (len(vib_rows) - len(vib_rows)//2)
        vib_slope = round(recent - older, 2)
        if vib_slope > 0.4:
            vib_trend = "INCREASING (Deterioration)"
        elif vib_slope < -0.4:
            vib_trend = "DECREASING (Stabilized)"
        else:
            vib_trend = "STABLE (Normal)"

    # Status distribution for utilisation calculation
    cursor.execute("""
    SELECT status, COUNT(*) as count 
    FROM sensor_telemetry 
    WHERE machine_id = ? 
    GROUP BY status
    """, (machine_id,))
    status_counts = {r['status']: r['count'] for r in cursor.fetchall()}
    total = sum(status_counts.values()) if status_counts else 1
    
    normal_cnt = status_counts.get("NORMAL", 0) + status_counts.get("HIGH_LOAD", 0)
    warning_cnt = status_counts.get("WARNING", 0)
    critical_cnt = status_counts.get("CRITICAL", 0)

    utilisation = {
        "active_percent": round((normal_cnt / total) * 100, 1),
        "warning_percent": round((warning_cnt / total) * 100, 1),
        "downtime_percent": round((critical_cnt / total) * 100, 1),
    }

    # Fetch latest telemetry and equipment metadata for instant health score
    cursor.execute("SELECT * FROM equipment WHERE machine_id = ?", (machine_id,))
    mach_row = cursor.fetchone()
    mach_info = dict(mach_row) if mach_row else {}

    cursor.execute("""
    SELECT * FROM sensor_telemetry 
    WHERE machine_id = ? 
    ORDER BY timestamp DESC 
    LIMIT 1
    """, (machine_id,))
    latest_row = cursor.fetchone()
    latest_telemetry = dict(latest_row) if latest_row else None

    health_info = None
    if latest_telemetry and mach_info:
        from analytics import compute_equipment_health
        health_info = compute_equipment_health(
            temperature=latest_telemetry["temperature"],
            vibration=latest_telemetry["vibration"],
            pressure=latest_telemetry["pressure"],
            power=latest_telemetry["power"],
            nominal_temp=mach_info.get("nominal_temp", 55.0),
            nominal_vib=mach_info.get("nominal_vibration", 1.8),
            nominal_pressure=mach_info.get("nominal_pressure", 5.0),
            nominal_power=mach_info.get("nominal_power", 20.0)
        )

    conn.close()

    return {
        "machine_id": machine_id,
        "avg_temperature": round(row['avg_temp'] or 0.0, 1),
        "max_temperature": round(row['max_temp'] or 0.0, 1),
        "min_temperature": round(row['min_temp'] or 0.0, 1),
        "avg_vibration": round(row['avg_vibration'] or 0.0, 2),
        "max_vibration": round(row['max_vibration'] or 0.0, 2),
        "vibration_trend": vib_trend,
        "vibration_slope": vib_slope,
        "avg_power_kw": round(row['avg_power'] or 0.0, 2),
        "energy_consumed_kwh": round(row['energy_kwh'] or 0.0, 3),
        "total_readings": row['total_samples'] or 0,
        "utilisation": utilisation,
        "latest_telemetry": latest_telemetry,
        "health": health_info
    }
