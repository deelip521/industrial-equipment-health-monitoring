"""
IoT Sensor Simulator & Telemetry Streaming Engine
Simulates industrial machinery sensors (Temperature, Vibration, Pressure, Power)
and streams telemetry into the time-series store and connected dashboard clients.
"""
import time
import random
import threading
from datetime import datetime
from typing import Dict, Any, Callable, Optional
from database import insert_telemetry, insert_alert, get_all_machines
from analytics import compute_equipment_health, evaluate_alert_rules

class MachineSensorSimulator:
    def __init__(self, machine_config: Dict[str, Any]):
        self.machine_id = machine_config["machine_id"]
        self.name = machine_config["name"]
        self.nominal_temp = machine_config["nominal_temp"]
        self.nominal_vib = machine_config["nominal_vibration"]
        self.nominal_pressure = machine_config["nominal_pressure"]
        self.nominal_power = machine_config["nominal_power"]
        
        # State: NORMAL, OVERHEAT, VIBRATION_SPIKE, HIGH_LOAD, CRITICAL_DEGRADE
        self.mode = "NORMAL"
        self.mode_timer = 0
        
        # Current simulated values
        self.current_temp = self.nominal_temp
        self.current_vib = self.nominal_vib
        self.current_pressure = self.nominal_pressure
        self.current_power = self.nominal_power

    def set_mode(self, mode: str, duration_cycles: int = 40):
        self.mode = mode
        self.mode_timer = duration_cycles
        if mode == "OVERHEAT":
            self.current_temp = random.uniform(84.0, 89.5)
        elif mode == "VIBRATION_SPIKE":
            self.current_vib = random.uniform(5.8, 7.5)
        elif mode == "CRITICAL_DEGRADE":
            self.current_temp = random.uniform(87.0, 93.0)
            self.current_vib = random.uniform(6.5, 8.8)
            self.current_pressure = random.uniform(1.2, 1.8)
        elif mode == "HIGH_LOAD":
            self.current_temp = self.nominal_temp + 10.0
            self.current_power = self.nominal_power * 1.35
        elif mode == "NORMAL":
            self.current_temp = self.nominal_temp
            self.current_vib = self.nominal_vib
            self.current_pressure = self.nominal_pressure
            self.current_power = self.nominal_power

    def step(self) -> Dict[str, Any]:
        """Advances simulator by one telemetry sampling cycle."""
        if self.mode_timer > 0:
            self.mode_timer -= 1
            if self.mode_timer == 0:
                self.mode = "NORMAL"

        # Apply behavior based on current operating mode
        if self.mode == "NORMAL":
            target_temp = self.nominal_temp + random.uniform(-1.5, 1.5)
            target_vib = self.nominal_vib + random.uniform(-0.15, 0.2)
            target_press = self.nominal_pressure + random.uniform(-0.2, 0.2)
            target_pwr = self.nominal_power + random.uniform(-0.8, 0.8)
            status_label = "NORMAL"

        elif self.mode == "HIGH_LOAD":
            target_temp = self.nominal_temp + random.uniform(8.0, 14.0)
            target_vib = self.nominal_vib + random.uniform(0.6, 1.2)
            target_press = self.nominal_pressure + random.uniform(0.4, 0.9)
            target_pwr = self.nominal_power * random.uniform(1.25, 1.4)
            status_label = "HIGH_LOAD"

        elif self.mode == "OVERHEAT":
            # Breaches Assignment Rule 1: Temperature > 80°C (typically 83°C - 94°C)
            target_temp = random.uniform(83.0, 93.5)
            target_vib = self.nominal_vib + random.uniform(0.5, 1.5)
            target_press = self.nominal_pressure + random.uniform(0.5, 1.5)
            target_pwr = self.nominal_power * random.uniform(1.3, 1.5)
            status_label = "WARNING" if target_temp < 90 else "CRITICAL"

        elif self.mode == "VIBRATION_SPIKE":
            # Breaches Assignment Rule 2: Vibration > 5.0 mm/s (typically 5.6 - 8.8 mm/s)
            target_temp = self.nominal_temp + random.uniform(3.0, 8.0)
            target_vib = random.uniform(5.4, 8.5)
            target_press = self.nominal_pressure + random.uniform(-0.5, 0.5)
            target_pwr = self.nominal_power * random.uniform(1.15, 1.35)
            status_label = "CRITICAL" if target_vib > 7.0 else "WARNING"

        elif self.mode == "CRITICAL_DEGRADE":
            # Severe compound anomaly
            target_temp = random.uniform(87.0, 96.0)
            target_vib = random.uniform(6.5, 9.8)
            target_press = random.uniform(1.2, 2.5)  # loss of pressure
            target_pwr = self.nominal_power * random.uniform(1.4, 1.7)
            status_label = "CRITICAL"
        else:
            target_temp = self.nominal_temp
            target_vib = self.nominal_vib
            target_press = self.nominal_pressure
            target_pwr = self.nominal_power
            status_label = "NORMAL"

        # Smooth gradual progression (first-order low-pass filter)
        alpha = 0.35
        self.current_temp = round(alpha * target_temp + (1 - alpha) * self.current_temp, 2)
        self.current_vib = round(alpha * target_vib + (1 - alpha) * self.current_vib, 2)
        self.current_pressure = round(alpha * target_press + (1 - alpha) * self.current_pressure, 2)
        self.current_power = round(alpha * target_pwr + (1 - alpha) * self.current_power, 2)

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Compute health diagnostics
        health_info = compute_equipment_health(
            temperature=self.current_temp,
            vibration=self.current_vib,
            pressure=self.current_pressure,
            power=self.current_power,
            nominal_temp=self.nominal_temp,
            nominal_vib=self.nominal_vib,
            nominal_pressure=self.nominal_pressure,
            nominal_power=self.nominal_power
        )

        telemetry = {
            "machine_id": self.machine_id,
            "timestamp": timestamp_str,
            "temperature": self.current_temp,
            "vibration": self.current_vib,
            "pressure": self.current_pressure,
            "power": self.current_power,
            "status": health_info["status"]
        }

        # Check alert rules
        alerts = evaluate_alert_rules(
            machine_id=self.machine_id,
            timestamp=timestamp_str,
            temperature=self.current_temp,
            vibration=self.current_vib,
            pressure=self.current_pressure,
            power=self.current_power
        )

        return {
            "telemetry": telemetry,
            "health": health_info,
            "alerts": alerts,
            "mode": self.mode
        }


class IoTStreamingEngine:
    """Manages multi-machine simulation and continuous broadcast."""
    def __init__(self):
        self.simulators: Dict[str, MachineSensorSimulator] = {}
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.broadcast_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.sample_interval = 2.0  # seconds

    def initialize(self):
        machines = get_all_machines()
        for m in machines:
            self.simulators[m["machine_id"]] = MachineSensorSimulator(m)
        print(f"[IoT Streaming Engine] Initialized {len(self.simulators)} industrial machines.")

    def set_machine_mode(self, machine_id: str, mode: str, duration: int = 40):
        if machine_id in self.simulators:
            self.simulators[machine_id].set_mode(mode, duration)
            return True
        return False

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[IoT Streaming Engine] Sensor streaming thread started.")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        print("[IoT Streaming Engine] Sensor streaming thread stopped.")

    def _run_loop(self):
        last_alert_time: Dict[str, float] = {}

        while self.is_running:
            batch_data = {}
            for machine_id, sim in self.simulators.items():
                data = sim.step()
                telemetry = data["telemetry"]
                health = data["health"]
                alerts = data["alerts"]

                # Store in SQLite time-series
                insert_telemetry(telemetry)

                # Persist alerts with throttle to avoid spamming the log
                now_ts = time.time()
                for alert in alerts:
                    alert_key = f"{machine_id}_{alert['rule_triggered']}"
                    if now_ts - last_alert_time.get(alert_key, 0) > 10.0:  # 10s cooldown per alert rule
                        insert_alert(alert)
                        last_alert_time[alert_key] = now_ts

                batch_data[machine_id] = {
                    "telemetry": telemetry,
                    "health": health,
                    "alerts": alerts,
                    "mode": sim.mode
                }

            # Broadcast to web dashboard
            if self.broadcast_callback:
                try:
                    self.broadcast_callback(batch_data)
                except Exception as e:
                    pass

            time.sleep(self.sample_interval)

# Global streaming engine instance
streaming_engine = IoTStreamingEngine()
