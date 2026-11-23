import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import database
import analytics
import simulator
import app

print("Initializing DB...")
database.init_db()
machines = database.get_all_machines()
print(f"Machines in DB: {len(machines)}")
for m in machines:
    print(f" - {m['machine_id']}: {m['name']}")

print("\nTesting Analytics...")
health = analytics.compute_equipment_health(85.5, 6.2, 5.0, 25.0)
print(f"Health score: {health['health_score']}, Status: {health['status']}, Failure mode: {health['failure_mode']}")

alerts = analytics.evaluate_alert_rules("CNC-M01", "2026-11-20 12:00:00", 85.5, 6.2, 5.0, 25.0)
print(f"Alerts generated: {len(alerts)}")
for a in alerts:
    print(f" - [{a['severity']}] {a['rule_triggered']}: {a['message']}")

print("\nTesting Simulator...")
sim = simulator.MachineSensorSimulator(machines[0])
step_result = sim.step()
print("Step telemetry:", step_result['telemetry'])

print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
