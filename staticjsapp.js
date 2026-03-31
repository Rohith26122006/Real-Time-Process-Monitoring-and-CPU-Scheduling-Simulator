/**
 * Real-Time Process Monitoring and CPU Scheduling Simulator
 * Frontend JavaScript - Handles UI updates and API communication
 * Team: Lovepreet Singh, Piyush Dhami, Vennam Siddu
 */

// ============================================
// GLOBAL VARIABLES
// ============================================

let pollingInterval = null;
let currentState = null;
let simulationSpeed = 500;
let isPolling = false;

// Color mapping for processes
const processColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec489a', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
];

// ============================================
// API CALLS
// ============================================

async function apiGet(endpoint) {
    try {
        const response = await fetch(endpoint);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

async function apiPost(endpoint, data = {}) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

// ============================================
// SIMULATION CONTROLS
// ============================================

async function startSim() {
    await apiPost('/api/start');
    startPolling();
    updateButtonStates(true);
}

async function pauseSim() {
    await apiPost('/api/pause');
    updateButtonStates(false);
}

async function stepSim() {
    await apiPost('/api/step');
    await fetchState();
}

async function resetSim() {
    await apiPost('/api/reset');
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    await fetchState();
    updateButtonStates(false);
    document.getElementById('event-log').innerHTML = '<div class="event-entry">System reset. Ready for new simulation.</div>';
}

async function addProcess() {
    const process = {
        name: document.getElementById('proc-name').value || 'P',
        arrival: parseInt(document.getElementById('proc-arrival').value) || 0,
        burst: parseInt(document.getElementById('proc-burst').value) || 5,
        priority: parseInt(document.getElementById('proc-priority').value) || 5,
        memory: parseInt(document.getElementById('proc-memory').value) || 64,
        io_time: parseInt(document.getElementById('proc-io').value) || 0
    };
    
    if (process.burst < 1) {
        alert('Burst time must be at least 1');
        return;
    }
    
    await apiPost('/api/add_process', process);
    await fetchState();
}

async function loadPreset() {
    await apiPost('/api/load_preset');
    await fetchState();
}

async function setAlgorithm(algo) {
    // Update UI
    document.querySelectorAll('.algo-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-algo="${algo}"]`).classList.add('active');
    
    // Show quantum control for Round Robin
    const quantumControl = document.getElementById('quantum-control');
    if (algo === 'RR') {
        quantumControl.style.display = 'block';
    } else {
        quantumControl.style.display = 'none';
    }
    
    // Send to backend
    const response = await apiPost('/api/set_scheduler', { algorithm: algo });
    if (response && response.scheduler) {
        document.getElementById('current-algo').textContent = response.scheduler;
    }
}

function updateQuantum(value) {
    document.getElementById('quantum-value').textContent = value;
    apiPost('/api/set_scheduler', { algorithm: 'RR', quantum: parseInt(value) });
}

function updateButtonStates(isRunning) {
    const startBtn = document.getElementById('btn-start');
    const pauseBtn = document.getElementById('btn-pause');
    const stepBtn = document.getElementById('btn-step');
    
    if (isRunning) {
        startBtn.disabled = true;
        pauseBtn.disabled = false;
        stepBtn.disabled = true;
    } else {
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        stepBtn.disabled = false;
    }
}

function clearLog() {
    document.getElementById('event-log').innerHTML = '';
}

// ============================================
// POLLING AND STATE UPDATE
// ============================================

function startPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    const speed = parseInt(document.getElementById('speed').value) || 500;
    simulationSpeed = speed;
    document.getElementById('speed-value').textContent = `${speed}ms`;
    
    pollingInterval = setInterval(fetchState, speed);
}

async function fetchState() {
    const state = await apiGet('/api/state');
    if (state) {
        currentState = state;
        updateUI(state);
    }
}

function updateUI(state) {
    // Update stats
    document.getElementById('stat-time').textContent = state.current_time;
    document.getElementById('stat-cpu').textContent = `${state.metrics.cpu_utilization}%`;
    document.getElementById('stat-avg-wait').textContent = state.metrics.avg_waiting_time;
    document.getElementById('stat-avg-tat').textContent = state.metrics.avg_turnaround_time;
    document.getElementById('stat-completed').textContent = state.metrics.completed;
    document.getElementById('stat-ctx').textContent = state.metrics.context_switches;
    document.getElementById('process-count').textContent = `${state.metrics.total_processes} processes`;
    
    // Update process table
    updateProcessTable(state.processes);
    
    // Update Gantt chart
    updateGanttChart(state.gantt_data);
    
    // Update event log
    updateEventLog(state.events);
}

function updateProcessTable(processes) {
    const tbody = document.getElementById('process-table-body');
    
    if (!processes || processes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">No processes added</td></tr>';
        return;
    }
    
    tbody.innerHTML = processes.map(p => `
        <tr>
            <td><strong style="color: ${getProcessColor(p.pid)}">${p.pid}</strong></td>
            <td>${p.name}</td>
            <td><span class="state-badge state-${p.state}">${p.state.toUpperCase()}</span></td>
            <td>${p.arrival_time}</td>
            <td>${p.burst_time}</td>
            <td>${p.remaining_time}</td>
            <td>${p.priority}</td>
            <td>${p.waiting_time || 0}</td>
            <td>${p.turnaround_time || '-'}</td>
            <td>${p.response_time || '-'}</td>
        </tr>
    `).join('');
}

function updateGanttChart(ganttData) {
    const container = document.getElementById('gantt-container');
    
    if (!ganttData || ganttData.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">Run simulation to see Gantt chart</div>';
        return;
    }
    
    // Group by process
    const byProcess = {};
    for (const block of ganttData) {
        if (!byProcess[block.pid]) {
            byProcess[block.pid] = [];
        }
        byProcess[block.pid].push(block);
    }
    
    let html = '';
    for (const [pid, blocks] of Object.entries(byProcess)) {
        const color = pid === 'IDLE' ? '#2d3748' : getProcessColor(parseInt(pid));
        html += `
            <div class="gantt-row">
                <div class="gantt-label" style="color: ${color}">${pid === 'IDLE' ? 'IDLE' : `P${pid}`}</div>
                <div class="gantt-blocks">
                    ${blocks.map(block => `
                        <div class="gantt-block" style="background: ${color}20; border-left: 2px solid ${color}; width: ${Math.max(30, (block.end - block.start) * 5)}px"
                             title="${pid === 'IDLE' ? 'IDLE' : `Process ${pid}`}: ${block.start} → ${block.end}">
                            ${block.end - block.start}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function updateEventLog(events) {
    const logContainer = document.getElementById('event-log');
    
    if (!events || events.length === 0) return;
    
    // Only add new events (simplified - just show last 20)
    const latestEvents = events.slice(-20);
    logContainer.innerHTML = latestEvents.map(e => `
        <div class="event-entry">
            <span class="time">[${e.time}]</span>
            <span>${e.message}</span>
        </div>
    `).join('');
    
    // Auto-scroll
    logContainer.scrollTop = logContainer.scrollHeight;
}

function getProcessColor(pid) {
    return processColors[pid % processColors.length];
}

// ============================================
// SPEED CONTROL
// ============================================

document.getElementById('speed').addEventListener('input', function(e) {
    const value = e.target.value;
    document.getElementById('speed-value').textContent = `${value}ms`;
    if (pollingInterval) {
        startPolling(); // Restart with new speed
    }
});

// ============================================
// INITIALIZATION
// ============================================

window.addEventListener('DOMContentLoaded', async () => {
    // Initial state fetch
    await fetchState();
    
    // Set default algorithm
    setAlgorithm('FCFS');
    
    // Load preset for demo
    await loadPreset();
    
    console.log('Simulator ready');
});