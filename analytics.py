"""
Analytics & Predictive Maintenance Module
Implements multi-sensor health scoring, anomaly detection, failure prediction indicators,
and Remaining Useful Life (RUL) estimation.
"""
import math
from typing import Dict, Any, List

# Threshold Constants based on Industrial ISO 10816 Standards and assignment specifications
TEMP_ALERT_THRESHOLD = 80.0       # Assignment Rule: Temperature > 80°C
VIBRATION_ALERT_THRESHOLD = 5.0  # Assignment Rule: Vibration > Threshold (5.0 mm/s ISO limit for Class III/IV)
PRESSURE_LOW_THRESHOLD = 2.0     # Underpressure warning
PRESSURE_HIGH_THRESHOLD = 9.0    # Overpressure hazard

def compute_equipment_health(
    temperature: float,
    vibration: float,
    pressure: float,
    power: float,
    nominal_temp: float = 55.0,
    nominal_vib: float = 1.8,
    nominal_pressure: float = 5.0,
    nominal_power: float = 20.0
) -> Dict[str, Any]:
    """
    Computes real-time equipment health score (0-100), failure risk %, RUL, and diagnostics.
    """
    # 1. Temperature Penalty (Weight: 35%)
    # Below nominal is healthy. Above 80°C takes severe degradation.
    temp_diff = max(0.0, temperature - nominal_temp)
    if temperature > TEMP_ALERT_THRESHOLD:
        temp_penalty = 35.0 * min(1.0, (temperature - TEMP_ALERT_THRESHOLD) / 20.0 + 0.6)
    else:
        temp_penalty = 35.0 * (temp_diff / (TEMP_ALERT_THRESHOLD - nominal_temp + 0.001)) * 0.4

    # 2. Vibration Penalty (Weight: 40% - critical for bearing/rotary mechanical health)
    vib_diff = max(0.0, vibration - nominal_vib)
    if vibration > VIBRATION_ALERT_THRESHOLD:
        vib_penalty = 40.0 * min(1.0, (vibration - VIBRATION_ALERT_THRESHOLD) / 4.0 + 0.6)
    else:
        vib_penalty = 40.0 * (vib_diff / (VIBRATION_ALERT_THRESHOLD - nominal_vib + 0.001)) * 0.35

    # 3. Pressure Penalty (Weight: 15%)
    pressure_diff = abs(pressure - nominal_pressure)
    pressure_penalty = 15.0 * min(1.0, pressure_diff / 4.0)

    # 4. Power Anomaly Penalty (Weight: 10%)
    power_diff = max(0.0, power - (nominal_power * 1.3))
    power_penalty = 10.0 * min(1.0, power_diff / (nominal_power * 0.5 + 0.001))

    total_penalty = temp_penalty + vib_penalty + pressure_penalty + power_penalty
    health_score = max(5.0, min(100.0, 100.0 - total_penalty))
    health_score = round(health_score, 1)

    # Failure Risk Calculation (Logistic Sigmoid Model)
    # Risk increases exponentially as health degrades below 75%
    z = (70.0 - health_score) / 12.0
    failure_risk_pct = round(100.0 / (1.0 + math.exp(-z)), 1)

    # Estimated Remaining Useful Life (RUL in operating hours)
    # A perfectly healthy machine has ~2400-3000 running hours until scheduled major overhaul.
    # When health is critical (<40%), RUL collapses to <48 hours.
    if health_score >= 85:
        rul_hours = int(1800 + (health_score - 85) * 50)
        status = "NORMAL"
        diagnostic = "Optimal mechanical condition. All sensor parameters within baseline."
        recommendation = "Continue standard operating schedule. Next routine inspection in 30 days."
    elif health_score >= 65:
        rul_hours = int(500 + (health_score - 65) * 60)
        status = "WARNING"
        diagnostic = "Moderate operational stress detected. Elevated thermal or vibration signature."
        recommendation = "Schedule preventative diagnostic scan and check lubrication levels within 7 days."
    elif health_score >= 40:
        rul_hours = int(72 + (health_score - 40) * 15)
        status = "HIGH_RISK"
        diagnostic = "Significant degradation! Approaching ISO mechanical vibration or thermal limit."
        recommendation = "Plan immediate maintenance shutdown within 48h. Inspect bearings and cooling loops."
    else:
        rul_hours = max(2, int((health_score / 40.0) * 48))
        status = "CRITICAL"
        diagnostic = "CRITICAL FAILURE IMMINENT! Sensor readings exceed safety shutdown thresholds."
        recommendation = "EMERGENCY TRIP REQUIRED! Halt equipment immediately to prevent catastrophic seizure."

    # Specific Failure Prediction Indicators
    failure_mode = "None (Healthy)"
    if vibration > VIBRATION_ALERT_THRESHOLD and temperature > TEMP_ALERT_THRESHOLD:
        failure_mode = "Compound Failure: Bearing Seizure & Overheating"
    elif vibration > VIBRATION_ALERT_THRESHOLD:
        failure_mode = "Mechanical Defect: Bearing Wear / Imbalance / Misalignment"
    elif temperature > TEMP_ALERT_THRESHOLD:
        failure_mode = "Thermal Overload: Coolant Failure / Friction Spike"
    elif pressure < PRESSURE_LOW_THRESHOLD:
        failure_mode = "Hydraulic / Pneumatic Loss: Seal Leakage Detected"
    elif pressure > PRESSURE_HIGH_THRESHOLD:
        failure_mode = "Pressure Line Blockage / Valve Malfunction"
    elif power > nominal_power * 1.4:
        failure_mode = "Electrical Stress: Motor Overloading / Inverter Distortion"

    return {
        "health_score": health_score,
        "failure_risk_pct": failure_risk_pct,
        "rul_hours": rul_hours,
        "status": status,
        "failure_mode": failure_mode,
        "diagnostic": diagnostic,
        "recommendation": recommendation,
        "penalties": {
            "temperature_penalty": round(temp_penalty, 1),
            "vibration_penalty": round(vib_penalty, 1),
            "pressure_penalty": round(pressure_penalty, 1),
            "power_penalty": round(power_penalty, 1)
        }
    }

def evaluate_alert_rules(
    machine_id: str,
    timestamp: str,
    temperature: float,
    vibration: float,
    pressure: float,
    power: float
) -> List[Dict[str, Any]]:
    """
    Evaluates rule-based alerting criteria specified in Assignment 23.
    Rule 1: Temperature > 80°C
    Rule 2: Vibration > Threshold (5.0 mm/s)
    """
    alerts = []

    # Rule 1: High Temperature Alert
    if temperature > TEMP_ALERT_THRESHOLD:
        severity = "CRITICAL" if temperature > 92.0 else "WARNING"
        alerts.append({
            "machine_id": machine_id,
            "timestamp": timestamp,
            "severity": severity,
            "rule_triggered": "RULE-01: HIGH_TEMPERATURE",
            "metric_name": "temperature",
            "metric_value": round(temperature, 1),
            "threshold_value": TEMP_ALERT_THRESHOLD,
            "message": f"Temperature exceeded safe threshold: {temperature:.1f}°C > {TEMP_ALERT_THRESHOLD}°C"
        })

    # Rule 2: High Vibration Alert
    if vibration > VIBRATION_ALERT_THRESHOLD:
        severity = "CRITICAL" if vibration > 7.5 else "WARNING"
        alerts.append({
            "machine_id": machine_id,
            "timestamp": timestamp,
            "severity": severity,
            "rule_triggered": "RULE-02: EXCESSIVE_VIBRATION",
            "metric_name": "vibration",
            "metric_value": round(vibration, 2),
            "threshold_value": VIBRATION_ALERT_THRESHOLD,
            "message": f"Vibration velocity surpassed ISO threshold: {vibration:.2f} mm/s > {VIBRATION_ALERT_THRESHOLD} mm/s"
        })

    # Additional Safety Guardrails: Pressure & Power
    if pressure < PRESSURE_LOW_THRESHOLD or pressure > PRESSURE_HIGH_THRESHOLD:
        alerts.append({
            "machine_id": machine_id,
            "timestamp": timestamp,
            "severity": "WARNING",
            "rule_triggered": "RULE-03: PRESSURE_ANOMALY",
            "metric_name": "pressure",
            "metric_value": round(pressure, 2),
            "threshold_value": PRESSURE_HIGH_THRESHOLD,
            "message": f"Operating pressure abnormal: {pressure:.2f} bar outside safe window ({PRESSURE_LOW_THRESHOLD}-{PRESSURE_HIGH_THRESHOLD} bar)"
        })

    return alerts
