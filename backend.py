"""
Real-Time Process Monitoring and CPU Scheduling Simulator
Backend Server - Flask Application
Team: Lovepreet Singh, Piyush Dhami, Vennam Siddu
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import time
import heapq
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json

app = Flask(__name__)
CORS(app)

# ============================================
# DATA STRUCTURES
# ============================================

class ProcessState(Enum):
    """Process states in the operating system"""
    NEW = "new"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    TERMINATED = "terminated"

@dataclass
class Process:
    """Process Control Block (PCB)"""
    pid: int
    name: str
    arrival_time: int
    burst_time: int
    priority: int
    memory_required: int = 64
    io_time: int = 0
    
    # Dynamic attributes
    remaining_time: int = 0
    state: ProcessState = ProcessState.NEW
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    waiting_time: int = 0
    turnaround_time: int = 0
    response_time: Optional[int] = None
    last_run_time: int = 0
    
    def __post_init__(self):
        self.remaining_time = self.burst_time


# ============================================
# SCHEDULING ALGORITHMS
# ============================================

class Scheduler:
    """Base class for all scheduling algorithms"""
    
    def __init__(self, name: str):
        self.name = name
        self.context_switches = 0
    
    def schedule(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        """Select next process to run - to be implemented by subclasses"""
        raise NotImplementedError
    
    def should_preempt(self, current: Process, new: Process, current_time: int) -> bool:
        """Check if current process should be preempted"""
        return False


class FCFSScheduler(Scheduler):
    """First-Come-First-Served - Non-preemptive"""
    
    def __init__(self):
        super().__init__("FCFS")
    
    def schedule(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        # Sort by arrival time, then by PID
        ready_queue.sort(key=lambda p: (p.arrival_time, p.pid))
        return ready_queue[0]


class SJFScheduler(Scheduler):
    """Shortest Job First - Non-preemptive"""
    
    def __init__(self):
        super().__init__("SJF")
    
    def schedule(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        # Sort by burst time (shortest first), then by arrival
        ready_queue.sort(key=lambda p: (p.burst_time, p.arrival_time, p.pid))
        return ready_queue[0]


class SRTFScheduler(Scheduler):
    """Shortest Remaining Time First - Preemptive"""
    
    def __init__(self):
        super().__init__("SRTF")
    
    def schedule(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        # Sort by remaining time
        ready_queue.sort(key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
        return ready_queue[0]
    
    def should_preempt(self, current: Process, new: Process, current_time: int) -> bool:
        return new.remaining_time < current.remaining_time


class PriorityScheduler(Scheduler):
    """Priority Scheduling - Lower number = Higher priority"""
    
    def __init__(self, preemptive: bool = False):
        super().__init__(f"Priority{' (Preemptive)' if preemptive else ''}")
        self.preemptive = preemptive
    
    def schedule(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        # Sort by priority (lower = higher priority), then by arrival
        ready_queue.sort(key=lambda p: (p.priority, p.arrival_time, p.pid))
        return ready_queue[0]
    
    def should_preempt(self, current: Process, new: Process, current_time: int) -> bool:
        if not self.preemptive:
            return False
        return new.priority < current.priority


class RoundRobinScheduler(Scheduler):
    """Round Robin with time quantum"""
    
    def __init__(self, quantum: int = 4):
        super().__init__(f"Round Robin (Q={quantum})")
        self.quantum = quantum
    
    def schedule(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        # Round Robin - circular queue (FIFO)
        return ready_queue[0]
    
    def should_preempt(self, current: Process, new: Process, current_time: int) -> bool:
        # Round Robin uses time quantum, not process-based preemption
        return False


# ============================================
# SIMULATION ENGINE
# ============================================

class SimulationEngine:
    """Core simulation engine managing processes and scheduling"""
    
    def __init__(self):
        self.processes: Dict[int, Process] = {}
        self.next_pid = 1
        self.current_time = 0
        self.is_running = False
        self.is_paused = False
        self.scheduler = FCFSScheduler()
        self.quantum = 4
        self.current_process: Optional[Process] = None
        self.time_slice_used = 0
        self.gantt_data: List[Dict] = []
        self.event_log: List[Dict] = []
        self.stats = {
            'context_switches': 0,
            'total_burst_time': 0,
            'cpu_busy_time': 0
        }
        self.lock = threading.Lock()
    
    def add_process(self, name: str, arrival: int, burst: int, priority: int = 5, 
                    memory: int = 64, io_time: int = 0) -> Process:
        """Add a new process to the simulation"""
        with self.lock:
            pid = self.next_pid
            self.next_pid += 1
            
            process = Process(
                pid=pid,
                name=name or f"P{pid}",
                arrival_time=arrival,
                burst_time=burst,
                priority=priority,
                memory_required=memory,
                io_time=io_time
            )
            process.state = ProcessState.NEW
            self.processes[pid] = process
            self.stats['total_burst_time'] += burst
            
            self._log_event(f"Process {process.name} created (Burst={burst}, Priority={priority}, Arrival={arrival})")
            return process
    
    def set_scheduler(self, algo_name: str):
        """Change the scheduling algorithm"""
        with self.lock:
            algo_map = {
                'FCFS': FCFSScheduler,
                'SJF': SJFScheduler,
                'SRTF': SRTFScheduler,
                'PRIORITY': lambda: PriorityScheduler(preemptive=False),
                'PRIORITY_P': lambda: PriorityScheduler(preemptive=True),
                'RR': lambda: RoundRobinScheduler(self.quantum)
            }
            
            if algo_name in algo_map:
                self.scheduler = algo_map[algo_name]()
                self._log_event(f"Scheduler changed to {self.scheduler.name}")
    
    def set_quantum(self, quantum: int):
        """Set time quantum for Round Robin"""
        self.quantum = quantum
        if isinstance(self.scheduler, RoundRobinScheduler):
            self.scheduler.quantum = quantum
            self.scheduler.name = f"Round Robin (Q={quantum})"
    
    def _get_ready_queue(self) -> List[Process]:
        """Get all processes in READY state, sorted by scheduler logic"""
        ready = [p for p in self.processes.values() if p.state == ProcessState.READY]
        # Let scheduler determine order
        return ready
    
    def _update_arrivals(self):
        """Move processes from NEW to READY when arrival time reached"""
        for p in self.processes.values():
            if p.state == ProcessState.NEW and p.arrival_time <= self.current_time:
                p.state = ProcessState.READY
                self._log_event(f"Process {p.name} arrived at time {self.current_time}")
    
    def _select_next_process(self) -> Optional[Process]:
        """Select next process using current scheduler"""
        ready_queue = self._get_ready_queue()
        if not ready_queue:
            return None
        return self.scheduler.schedule(ready_queue, self.current_time)
    
    def _execute_process(self, process: Process) -> bool:
        """Execute process for one time unit, return True if completed"""
        # First time running? Set start and response time
        if process.start_time is None:
            process.start_time = self.current_time
            process.response_time = self.current_time - process.arrival_time
            self._log_event(f"Process {process.name} started execution at time {self.current_time}")
        
        # Execute one unit
        process.remaining_time -= 1
        process.last_run_time = self.current_time
        
        # Check if completed
        if process.remaining_time <= 0:
            process.completion_time = self.current_time + 1
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time
            process.state = ProcessState.TERMINATED
            self._log_event(f"Process {process.name} completed at time {process.completion_time} "
                          f"(Turnaround={process.turnaround_time}, Waiting={process.waiting_time})")
            return True
        
        return False
    
    def _handle_io_block(self, process: Process):
        """Handle I/O operation - moves process to WAITING state"""
        if process.io_time > 0:
            process.state = ProcessState.WAITING
            self._log_event(f"Process {process.name} blocked on I/O for {process.io_time} units")
            # In a real simulation, we'd have a separate I/O queue
            # For simplicity, we'll handle this in the main loop
    
    def tick(self) -> Dict:
        """Execute one simulation tick"""
        with self.lock:
            if not self.is_running or self.is_paused:
                return self.get_state()
            
            # Update arrivals
            self._update_arrivals()
            
            # Handle process execution
            previous_process = self.current_process
            
            if self.current_process:
                # Check if time quantum expired (Round Robin)
                if isinstance(self.scheduler, RoundRobinScheduler):
                    self.time_slice_used += 1
                    if self.time_slice_used >= self.quantum:
                        if self.current_process.state == ProcessState.RUNNING:
                            self.current_process.state = ProcessState.READY
                            self._log_event(f"Time quantum expired for {self.current_process.name} at time {self.current_time}")
                            self.current_process = None
                            self.stats['context_switches'] += 1
                            self.time_slice_used = 0
            
            # If no process running, select one
            if not self.current_process or self.current_process.state != ProcessState.RUNNING:
                next_process = self._select_next_process()
                
                if next_process:
                    # Preemption check
                    if self.current_process and self.scheduler.should_preempt(self.current_process, next_process, self.current_time):
                        self.current_process.state = ProcessState.READY
                        self._log_event(f"Process {next_process.name} preempted {self.current_process.name} at time {self.current_time}")
                        self.stats['context_switches'] += 1
                    
                    next_process.state = ProcessState.RUNNING
                    self.current_process = next_process
                    
                    if previous_process != self.current_process:
                        self.stats['context_switches'] += 1
                        if previous_process:
                            self._log_event(f"Context switch: {previous_process.name} → {self.current_process.name}")
            
            # Execute current process
            if self.current_process and self.current_process.state == ProcessState.RUNNING:
                completed = self._execute_process(self.current_process)
                
                # Track CPU busy time
                self.stats['cpu_busy_time'] += 1
                
                # Add to Gantt chart
                if self.gantt_data and self.gantt_data[-1]['pid'] == self.current_process.pid:
                    self.gantt_data[-1]['end'] = self.current_time + 1
                else:
                    self.gantt_data.append({
                        'pid': self.current_process.pid,
                        'name': self.current_process.name,
                        'start': self.current_time,
                        'end': self.current_time + 1
                    })
                
                if completed:
                    self.current_process = None
            else:
                # CPU idle
                if self.gantt_data and self.gantt_data[-1]['pid'] == 'IDLE':
                    self.gantt_data[-1]['end'] = self.current_time + 1
                else:
                    self.gantt_data.append({
                        'pid': 'IDLE',
                        'name': 'IDLE',
                        'start': self.current_time,
                        'end': self.current_time + 1
                    })
            
            # Update waiting times for all ready processes
            for p in self.processes.values():
                if p.state == ProcessState.READY and p != self.current_process:
                    p.waiting_time += 1
            
            self.current_time += 1
            return self.get_state()
    
    def _log_event(self, message: str):
        """Add event to log"""
        self.event_log.append({
            'time': self.current_time,
            'message': message
        })
        # Keep last 100 events
        if len(self.event_log) > 100:
            self.event_log.pop(0)
    
    def start(self):
        """Start simulation"""
        self.is_running = True
        self.is_paused = False
        self._log_event(f"Simulation started with {self.scheduler.name}")
    
    def pause(self):
        """Pause simulation"""
        self.is_paused = True
        self._log_event("Simulation paused")
    
    def resume(self):
        """Resume simulation"""
        self.is_paused = False
        self._log_event("Simulation resumed")
    
    def step(self):
        """Execute one step"""
        self.is_running = True
        self.is_paused = False
        self.tick()
        self.pause()
    
    def reset(self):
        """Reset simulation"""
        with self.lock:
            self.processes.clear()
            self.next_pid = 1
            self.current_time = 0
            self.is_running = False
            self.is_paused = False
            self.current_process = None
            self.time_slice_used = 0
            self.gantt_data = []
            self.event_log = []
            self.stats = {
                'context_switches': 0,
                'total_burst_time': 0,
                'cpu_busy_time': 0
            }
            self._log_event("Simulation reset")
    
    def get_state(self) -> Dict:
        """Get current simulation state for frontend"""
        with self.lock:
            processes = []
            for p in self.processes.values():
                processes.append({
                    'pid': p.pid,
                    'name': p.name,
                    'state': p.state.value,
                    'arrival_time': p.arrival_time,
                    'burst_time': p.burst_time,
                    'remaining_time': p.remaining_time,
                    'priority': p.priority,
                    'memory': p.memory_required,
                    'waiting_time': p.waiting_time,
                    'turnaround_time': p.turnaround_time if p.completion_time else None,
                    'response_time': p.response_time,
                    'start_time': p.start_time,
                    'completion_time': p.completion_time
                })
            
            # Calculate metrics
            completed = [p for p in self.processes.values() if p.state == ProcessState.TERMINATED]
            avg_waiting = sum(p.waiting_time for p in completed) / len(completed) if completed else 0
            avg_turnaround = sum(p.turnaround_time for p in completed) / len(completed) if completed else 0
            avg_response = sum(p.response_time for p in completed if p.response_time) / len(completed) if completed else 0
            
            cpu_utilization = (self.stats['cpu_busy_time'] / max(self.current_time, 1)) * 100
            
            return {
                'current_time': self.current_time,
                'is_running': self.is_running,
                'is_paused': self.is_paused,
                'scheduler': self.scheduler.name,
                'quantum': self.quantum,
                'processes': processes,
                'gantt_data': self.gantt_data[-50:],  # Last 50 entries
                'events': self.event_log[-50:],
                'metrics': {
                    'total_processes': len(self.processes),
                    'completed': len(completed),
                    'avg_waiting_time': round(avg_waiting, 2),
                    'avg_turnaround_time': round(avg_turnaround, 2),
                    'avg_response_time': round(avg_response, 2),
                    'cpu_utilization': round(cpu_utilization, 1),
                    'context_switches': self.stats['context_switches'],
                    'throughput': len(completed) / max(self.current_time, 1)
                }
            }


# ============================================
# FLASK API ENDPOINTS
# ============================================

engine = SimulationEngine()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    """Get current simulation state"""
    return jsonify(engine.get_state())

@app.route('/api/start', methods=['POST'])
def start_simulation():
    """Start the simulation"""
    engine.start()
    return jsonify({'status': 'started'})

@app.route('/api/pause', methods=['POST'])
def pause_simulation():
    """Pause the simulation"""
    engine.pause()
    return jsonify({'status': 'paused'})

@app.route('/api/resume', methods=['POST'])
def resume_simulation():
    """Resume the simulation"""
    engine.resume()
    return jsonify({'status': 'resumed'})

@app.route('/api/step', methods=['POST'])
def step_simulation():
    """Execute one simulation step"""
    engine.step()
    return jsonify({'status': 'stepped'})

@app.route('/api/reset', methods=['POST'])
def reset_simulation():
    """Reset the simulation"""
    engine.reset()
    return jsonify({'status': 'reset'})

@app.route('/api/add_process', methods=['POST'])
def add_process():
    """Add a new process"""
    data = request.json
    process = engine.add_process(
        name=data.get('name', ''),
        arrival=int(data.get('arrival', 0)),
        burst=int(data.get('burst', 5)),
        priority=int(data.get('priority', 5)),
        memory=int(data.get('memory', 64)),
        io_time=int(data.get('io_time', 0))
    )
    return jsonify({
        'status': 'added',
        'process': {
            'pid': process.pid,
            'name': process.name
        }
    })

@app.route('/api/set_scheduler', methods=['POST'])
def set_scheduler():
    """Change scheduling algorithm"""
    data = request.json
    algo = data.get('algorithm', 'FCFS')
    engine.set_scheduler(algo)
    if 'quantum' in data:
        engine.set_quantum(int(data['quantum']))
    return jsonify({'status': 'updated', 'scheduler': engine.scheduler.name})

@app.route('/api/load_preset', methods=['POST'])
def load_preset():
    """Load a preset process set"""
    engine.reset()
    preset = [
        ('P1', 0, 8, 2, 128, 2),
        ('P2', 1, 4, 1, 64, 0),
        ('P3', 2, 9, 3, 256, 3),
        ('P4', 3, 5, 2, 96, 0),
        ('P5', 4, 2, 1, 64, 1)
    ]
    for name, arr, burst, pri, mem, io in preset:
        engine.add_process(name, arr, burst, pri, mem, io)
    return jsonify({'status': 'preset_loaded', 'count': len(preset)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)