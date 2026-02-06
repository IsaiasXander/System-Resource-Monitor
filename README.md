# 🖥️ System Resource Monitor & Logger

> **Automated Energy & Hardware Tracking System**
>
> *Developed by Isaias Xander*

This project is a background monitoring agent designed to track **CPU & GPU usage patterns** and calculate real-time energy consumption costs. It uses a silent Python agent for data collection and a Streamlit dashboard for data visualization.

---

### 🛠️ Tech Stack
* **Core Logic:** Python 3.10+
* **Hardware Interaction:** `psutil` (CPU/RAM), `pynvml` (NVIDIA GPU)
* **Persistence:** SQLite3 (Local Relational DB)
* **Visualization:** Streamlit (Reactive Web Dashboard)
* **Automation:** `.pyw` background execution

### 🚀 Key Features
* **Silent Monitoring:** The `monitor_pc.pyw` script runs as a background process, logging metrics every 15 minutes without interrupting user workflow.
* **Smart Logging:** Implements logic to detect "idle" vs "load" states to optimize database storage.
* **Fail-Safe Architecture:** Data integrity checks ensure sessions are saved correctly even during unexpected power failures or system crashes.
* **Cost Calculation:** Estimates electricity costs based on configurable kWh rates and hardware power draw logic.

### ⚙️ How to Run
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/IsaiasXander/System-Resource-Monitor.git](https://github.com/IsaiasXander/System-Resource-Monitor.git)
    cd System-Resource-Monitor
    ```

2.  **Install dependencies:**
    ```bash
    pip install psutil pynvml streamlit
    ```

3.  **Start the Background Agent:**
    Double-click `scripts/monitor_pc.pyw` (Windows) or run:
    ```bash
    python scripts/monitor_pc.pyw
    ```

4.  **Launch the Dashboard:**
    ```bash
    streamlit run web/app.py
    ```

---
*Verified for Windows 10/11 Environments.*
