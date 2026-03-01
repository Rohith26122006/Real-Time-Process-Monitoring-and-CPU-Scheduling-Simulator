#  Real-Time Process Monitoring and CPU Scheduling Simulator

An interactive Operating System simulator that visualizes real-time CPU scheduling, process state transitions, and performance metrics.

---

##  Project Overview

The **Real-Time Process Monitoring and CPU Scheduling Simulator** is a web-based educational tool designed to demonstrate how operating systems manage processes and allocate CPU resources.

This simulator allows users to:
- Create processes dynamically
- Apply different CPU scheduling algorithms
- Monitor process states in real time
- Visualize execution using a Gantt chart
- Analyze performance metrics like Waiting Time, Turnaround Time, and CPU Utilization

The goal of this project is to bridge the gap between theoretical OS concepts and practical understanding through real-time visualization.

---

##  Features

### 🔹 Process Management
- Add processes dynamically
- Configure arrival time, burst time, and priority
- Display process lifecycle:
  - NEW
  - READY
  - RUNNING
  - WAITING
  - TERMINATED

### 🔹 Scheduling Algorithms Implemented
- First Come First Serve (FCFS)
- Shortest Job First (SJF)
- Shortest Remaining Time First (SRTF)
- Round Robin (RR)
- Priority Scheduling

### 🔹 Real-Time Simulation
- Tick-based execution
- Context switching simulation
- Ready queue visualization
- CPU allocation tracking

### 🔹 Performance Metrics
- Waiting Time
- Turnaround Time
- Response Time
- CPU Utilization
- Throughput
- Average Waiting Time

### 🔹 Visualization
- Live Process Table
- CPU Core Display
- Dynamic Gantt Chart
- Event Log Panel

---

##  System Architecture

The project follows a modular architecture:

### 1️ Backend (Scheduling Engine)
- Implements CPU scheduling algorithms
- Manages process states
- Executes simulation loop
- Calculates performance metrics

### 2️ Process Monitoring Module
- Tracks state transitions
- Computes metrics
- Maintains execution history

### 3️ Frontend Dashboard
- User interaction controls
- Real-time updates
- Graphical visualization

---

##  Technology Stack

### Programming Languages
- Python (Backend)
- JavaScript (Frontend)
- HTML5 / CSS3

### Libraries & Tools
- Flask (Backend API)
- Python Threading Module
- Chart.js (Gantt Chart Visualization)
- GitHub (Version Control)

---


