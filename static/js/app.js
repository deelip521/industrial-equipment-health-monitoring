/**
 * Frontend JavaScript for Industrial Equipment Health Monitoring System
 * Handles WebSocket telemetry streaming, Chart.js updates, analytics, and alert actions.
 */

let activeMachineId = "CNC-M01";
let machinesList = [];
let tempVibChart = null;
let pressPwrChart = null;
let telemetryHistory = [];
let lastWsUpdate = 0;
const MAX_DATA_POINTS = 30;

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", async () => {
    initCharts();
    await loadMachines();
    await loadInitialTelemetry();
    await loadAnalytics();
    await loadAlerts();
    initWebSocket();
    setupSimulatorButtons();

    // Fallback polling: if WebSocket is inactive or reconnecting, poll /api/telemetry/live
    setInterval(async () => {
        if (Date.now() - lastWsUpdate > 2500) {
            try {
                const res = await fetch('/api/telemetry/live');
                const data = await res.json();
                if (data && Object.keys(data).length > 0) {
                    handleLiveUpdate(data);
                }
            } catch (e) {}
        }
    }, 2000);

    // Auto refresh analytics & alerts
    setInterval(loadAnalytics, 5000);
    setInterval(loadAlerts, 6000);
});

// Setup Chart.js Charts
function initCharts() {
    const ctx1 = document.getElementById("tempVibChart").getContext("2d");
    tempVibChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    yAxisID: 'yTemp',
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 2
                },
                {
                    label: 'Vibration (mm/s)',
                    data: [],
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    yAxisID: 'yVib',
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: {
                    grid: { color: '#2b3649' },
                    ticks: { color: '#94a3b8', maxTicksLimit: 8 }
                },
                yTemp: {
                    type: 'linear',
                    position: 'left',
                    min: 20,
                    max: 110,
                    title: { display: true, text: 'Temp (°C)', color: '#ef4444' },
                    grid: { color: '#2b3649' },
                    ticks: { color: '#ef4444' }
                },
                yVib: {
                    type: 'linear',
                    position: 'right',
                    min: 0,
                    max: 10,
                    title: { display: true, text: 'Vibration (mm/s)', color: '#38bdf8' },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#38bdf8' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f1f5f9' } },
                tooltip: { backgroundColor: '#1e293b' }
            }
        }
    });

    const ctx2 = document.getElementById("pressPwrChart").getContext("2d");
    pressPwrChart = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Pressure (bar)',
                    data: [],
                    borderColor: '#10b981',
                    yAxisID: 'yPress',
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 2
                },
                {
                    label: 'Power (kW)',
                    data: [],
                    borderColor: '#eab308',
                    yAxisID: 'yPwr',
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    grid: { color: '#2b3649' },
                    ticks: { color: '#94a3b8', maxTicksLimit: 8 }
                },
                yPress: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    max: 12,
                    title: { display: true, text: 'Pressure (bar)', color: '#10b981' },
                    grid: { color: '#2b3649' },
                    ticks: { color: '#10b981' }
                },
                yPwr: {
                    type: 'linear',
                    position: 'right',
                    min: 0,
                    max: 60,
                    title: { display: true, text: 'Power (kW)', color: '#eab308' },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#eab308' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f1f5f9' } },
                tooltip: { backgroundColor: '#1e293b' }
            }
        }
    });
}

// Fetch list of machines and render selector
async function loadMachines() {
    try {
        const res = await fetch('/api/machines');
        machinesList = await res.json();
        const container = document.getElementById("machineSelectorBar");
        container.innerHTML = "";

        machinesList.forEach(m => {
            const chip = document.createElement("div");
            chip.className = `machine-chip ${m.machine_id === activeMachineId ? 'active' : ''}`;
            chip.id = `chip-${m.machine_id}`;
            chip.onclick = () => selectMachine(m.machine_id);

            chip.innerHTML = `
                <div>
                    <div class="chip-id">${m.machine_id}</div>
                    <div class="chip-type">${m.name}</div>
                </div>
                <div class="chip-status normal" id="chip-status-${m.machine_id}"></div>
            `;
            container.appendChild(chip);
        });
    } catch (e) {
        console.error("Failed to load machines:", e);
    }
}

function selectMachine(machineId) {
    activeMachineId = machineId;
    document.querySelectorAll('.machine-chip').forEach(c => c.classList.remove('active'));
    const target = document.getElementById(`chip-${machineId}`);
    if (target) target.classList.add('active');

    // Update active machine label
    document.getElementById("activeMachineTitle").textContent = machineId;
    const reportLink = document.getElementById("reportLink");
    if (reportLink) reportLink.href = `/report/${machineId}`;

    loadInitialTelemetry();
    loadAnalytics();
}

// Load historical telemetry for selected machine
async function loadInitialTelemetry() {
    try {
        const res = await fetch(`/api/telemetry/recent?machine_id=${activeMachineId}&limit=30`);
        const data = await res.json();
        telemetryHistory = data;
        renderTelemetryHistory();
    } catch (e) {
        console.error("Failed to load telemetry:", e);
    }
}

function renderTelemetryHistory() {
    const labels = telemetryHistory.map(d => d.timestamp.split(' ')[1]);
    const temps = telemetryHistory.map(d => d.temperature);
    const vibs = telemetryHistory.map(d => d.vibration);
    const pressures = telemetryHistory.map(d => d.pressure);
    const powers = telemetryHistory.map(d => d.power);

    tempVibChart.data.labels = labels;
    tempVibChart.data.datasets[0].data = temps;
    tempVibChart.data.datasets[1].data = vibs;
    tempVibChart.update();

    pressPwrChart.data.labels = labels;
    pressPwrChart.data.datasets[0].data = pressures;
    pressPwrChart.data.datasets[1].data = powers;
    pressPwrChart.update();

    if (telemetryHistory.length > 0) {
        const latest = telemetryHistory[telemetryHistory.length - 1];
        updateMetricCards(latest);
    }
}

// Update DOM cards for latest telemetry readings
function updateMetricCards(t, health = null) {
    // Temperature
    const tempVal = document.getElementById("valTemperature");
    tempVal.textContent = t.temperature.toFixed(1);
    if (t.temperature > 80.0) {
        tempVal.classList.add("val-alert");
        document.getElementById("badgeTemp").className = "card-badge badge critical";
        document.getElementById("badgeTemp").textContent = "ALERT >80°C";
    } else {
        tempVal.classList.remove("val-alert");
        document.getElementById("badgeTemp").className = "card-badge badge normal";
        document.getElementById("badgeTemp").textContent = "NORMAL (<80°C)";
    }

    // Vibration
    const vibVal = document.getElementById("valVibration");
    vibVal.textContent = t.vibration.toFixed(2);
    if (t.vibration > 5.0) {
        vibVal.classList.add("val-alert");
        document.getElementById("badgeVib").className = "card-badge badge critical";
        document.getElementById("badgeVib").textContent = "ALERT >5.0 mm/s";
    } else {
        vibVal.classList.remove("val-alert");
        document.getElementById("badgeVib").className = "card-badge badge normal";
        document.getElementById("badgeVib").textContent = "NORMAL (<5.0)";
    }

    // Pressure & Power
    document.getElementById("valPressure").textContent = t.pressure.toFixed(2);
    document.getElementById("valPower").textContent = t.power.toFixed(1);

    // Health Score & Predictive Diagnostics
    if (health) {
        const scoreElem = document.getElementById("healthScoreNumber");
        const circle = document.getElementById("healthCircle");
        scoreElem.textContent = health.health_score + "%";

        circle.className = "health-circle " + (
            health.health_score >= 80 ? "normal" : (health.health_score >= 50 ? "warning" : "critical")
        );

        document.getElementById("valFailureRisk").textContent = health.failure_risk_pct + "%";
        document.getElementById("valRulHours").textContent = health.rul_hours + " hrs";
        document.getElementById("valFailureMode").textContent = health.failure_mode;
        document.getElementById("diagnosticText").textContent = health.diagnostic;
        document.getElementById("prescriptiveActionText").textContent = health.recommendation;
    }
}

// WebSocket setup
function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/stream`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("[WebSocket] Connected to Industrial IoT Telemetry Stream");
        document.getElementById("streamStatusPill").style.display = "inline-flex";
    };

    socket.onmessage = (event) => {
        try {
            lastWsUpdate = Date.now();
            const msg = JSON.parse(event.data);
            if (msg.type === "TELEMETRY_UPDATE") {
                handleLiveUpdate(msg.data);
            }
        } catch (e) {
            console.error("WS Parse error", e);
        }
    };

    socket.onclose = () => {
        console.warn("[WebSocket] Disconnected. Reconnecting in 3s...");
        setTimeout(initWebSocket, 3000);
    };
}

function handleLiveUpdate(batch) {
    // Update chip indicators
    for (const [mid, data] of Object.entries(batch)) {
        const dot = document.getElementById(`chip-status-${mid}`);
        if (dot) {
            const st = data.health.status.toLowerCase();
            dot.className = `chip-status ${st === 'critical' ? 'critical' : (st === 'warning' ? 'warning' : 'normal')}`;
        }
    }

    // If active machine data received, update charts and cards
    if (batch[activeMachineId]) {
        const item = batch[activeMachineId];
        const t = item.telemetry;
        const timeLabel = t.timestamp.split(' ')[1];

        // Push to Chart 1
        tempVibChart.data.labels.push(timeLabel);
        tempVibChart.data.datasets[0].data.push(t.temperature);
        tempVibChart.data.datasets[1].data.push(t.vibration);
        if (tempVibChart.data.labels.length > MAX_DATA_POINTS) {
            tempVibChart.data.labels.shift();
            tempVibChart.data.datasets[0].data.shift();
            tempVibChart.data.datasets[1].data.shift();
        }
        tempVibChart.update('none');

        // Push to Chart 2
        pressPwrChart.data.labels.push(timeLabel);
        pressPwrChart.data.datasets[0].data.push(t.pressure);
        pressPwrChart.data.datasets[1].data.push(t.power);
        if (pressPwrChart.data.labels.length > MAX_DATA_POINTS) {
            pressPwrChart.data.labels.shift();
            pressPwrChart.data.datasets[0].data.shift();
            pressPwrChart.data.datasets[1].data.shift();
        }
        pressPwrChart.update('none');

        updateMetricCards(t, item.health);

        // If new alerts triggered in this step
        if (item.alerts && item.alerts.length > 0) {
            loadAlerts();
        }
    }
}

// Load Equipment Analytics
async function loadAnalytics() {
    try {
        const res = await fetch(`/api/analytics/${activeMachineId}`);
        const data = await res.json();
        document.getElementById("statAvgTemp").textContent = data.avg_temperature + "°C";
        document.getElementById("statVibTrend").textContent = data.vibration_trend;
        document.getElementById("statEnergyKwh").textContent = data.energy_consumed_kwh + " kWh";
        document.getElementById("statUtilisation").textContent = data.utilisation.active_percent + "%";

        // Update health dial and diagnostics from latest analytics if present
        if (data.health && data.latest_telemetry) {
            updateMetricCards(data.latest_telemetry, data.health);
        }
    } catch (e) {
        console.error("Failed to fetch analytics:", e);
    }
}

// Load Alerts table
async function loadAlerts() {
    try {
        const res = await fetch('/api/alerts?limit=25');
        const alerts = await res.json();
        const tbody = document.getElementById("alertsTableBody");
        tbody.innerHTML = "";

        if (alerts.length === 0) {
            tbody.innerHTML = "<tr><td colspan='6' style='text-align:center; color:#64748b; padding:16px;'>No recent alerts. All systems running safely within ISO parameters.</td></tr>";
            return;
        }

        alerts.forEach(a => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${a.timestamp}</td>
                <td><b>${a.machine_id}</b></td>
                <td><span class="badge ${a.severity.toLowerCase()}">${a.severity}</span></td>
                <td><code>${a.rule_triggered}</code></td>
                <td>${a.message}</td>
                <td>
                    ${a.status === 'ACTIVE' 
                        ? `<button class="btn-ack" onclick="acknowledgeAlert(${a.id})">Acknowledge</button>`
                        : `<span style="color:#64748b; font-size:11px;">ACKNOWLEDGED</span>`
                    }
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load alerts:", e);
    }
}

async function acknowledgeAlert(alertId) {
    await fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
    loadAlerts();
}

async function clearAllAlerts() {
    await fetch('/api/alerts/clear', { method: 'POST' });
    loadAlerts();
}

// Setup simulator injection buttons
function setupSimulatorButtons() {
    document.getElementById("btnSimNormal").onclick = () => injectFault("NORMAL");
    document.getElementById("btnSimOverheat").onclick = () => injectFault("OVERHEAT");
    document.getElementById("btnSimVibration").onclick = () => injectFault("VIBRATION_SPIKE");
    document.getElementById("btnSimHighLoad").onclick = () => injectFault("HIGH_LOAD");
    document.getElementById("btnSimCritical").onclick = () => injectFault("CRITICAL_DEGRADE");
    document.getElementById("btnClearAlerts").onclick = clearAllAlerts;
}

async function injectFault(mode) {
    try {
        await fetch('/api/simulator/mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ machine_id: activeMachineId, mode: mode, duration: 35 })
        });
        console.log(`Injected mode ${mode} into ${activeMachineId}`);
        // Immediate response update
        setTimeout(async () => {
            try {
                const res = await fetch('/api/telemetry/live');
                const batch = await res.json();
                if (batch && Object.keys(batch).length > 0) {
                    handleLiveUpdate(batch);
                }
                loadAlerts();
                loadAnalytics();
            } catch (e) {}
        }, 250);
    } catch (e) {
        console.error("Failed to inject simulation mode:", e);
    }
}
