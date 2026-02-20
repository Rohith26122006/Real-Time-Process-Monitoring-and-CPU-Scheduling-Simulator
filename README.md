cpu-scheduling-simulator/
│
├── 📁 src/
│   ├── main.(cpp/py/js)
│   │   ├── Entry point of the simulator
│   │   ├── Handles user input
│   │   ├── Initializes scheduler
│   │   └── Controls program execution flow
│   │
│   ├── process.(cpp/py/js)
│   │   ├── Defines Process class/structure
│   │   ├── Attributes:
│   │   │     • Process ID
│   │   │     • Arrival Time
│   │   │     • Burst Time
│   │   │     • Priority
│   │   │     • Remaining Time
│   │   │     • State (Ready, Running, Waiting, Terminated)
│   │   └── Methods for process state management
│   │
│   ├── scheduler.(cpp/py/js)
│   │   ├── Implements scheduling algorithms:
│   │   │     • FCFS
│   │   │     • SJF (Preemptive and Non-Preemptive)
│   │   │     • Round Robin
│   │   │     • Priority Scheduling
│   │   └── Controls CPU allocation logic
│   │
│   ├── queue.(cpp/py/js)
│   │   ├── Ready Queue implementation
│   │   ├── Waiting Queue implementation
│   │   └── Process insertion and removal logic
│   │
│   ├── metrics.(cpp/py/js)
│   │   ├── Calculates:
│   │   │     • Waiting Time
│   │   │     • Turnaround Time
│   │   │     • Response Time
│   │   │     • CPU Utilization
│   │   └── Displays performance results
│   │
│   └── gantt_chart.(cpp/py/js)
│         ├── Generates Gantt chart
│         ├── Displays execution timeline
│         └── Shows process switching visually
│
│
├── 📁 include/ (for C++ projects)
│   ├── process.h
│   ├── scheduler.h
│   ├── queue.h
│   ├── metrics.h
│   └── gantt_chart.h
│
│
├── 📁 data/
│   ├── sample_input.txt
│   │   ├── Contains predefined processes
│   │   └── Used for testing simulator
│   │
│   └── sample_output.txt
│
│
├── 📁 docs/
│   ├── Project_Report.pdf
│   ├── Algorithm_Explanation.pdf
│   ├── Flowchart.png
│   └── Screenshots/
│
│
├── 📁 ui/ (if GUI version)
│   ├── index.html
│   ├── style.css
│   └── script.js
│
│
├── README.md
│   ├── Project overview
│   ├── Installation instructions
│   ├── Usage guide
│   └── Example output
│
│
├── LICENSE
│
└── Makefile / requirements.txt / package.json
    ├── For compilation or dependency management
