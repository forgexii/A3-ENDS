# A3-ENDS: Adaptive AI-Driven Enterprise Network Defense System

A3-ENDS is a next-generation, real-time Network Intrusion Detection System (NIDS) designed to protect enterprise networks from both known cyber threats and zero-day anomalies. 

Built with a highly modular architecture, A3-ENDS combines the raw classification power of **XGBoost**, the baseline anomaly detection of a **Sparse Autoencoder**, and the continuous learning capabilities of a **Reinforcement Learning (RL)** agent. It also features a sleek, real-time **PyQt6 Desktop Dashboard** equipped with **SHAP Explainability** to help security analysts understand exactly *why* a threat was flagged.

## 🚀 Key Features

*   **Dual-Stage AI Pipeline:** A Sparse Autoencoder flags out-of-distribution volumetric anomalies, while an optimized 6-feature XGBoost model performs sub-millisecond multi-class threat classification.
*   **Adaptive Learning:** Integrates the ADWIN drift detection algorithm and a Q-Learning Reinforcement Learning agent to continuously adapt to evolving network topologies based on Human-In-The-Loop (HITL) feedback.
*   **Real-time Packet Capture:** Built-in `scapy` packet sniffer that dynamically binds to your active Network Interface Card (NIC) and tracks stateful TCP/UDP flow statistics (including Nmap port-scan aggregation).
*   **Explainable AI (XAI):** Uses SHAP (SHapley Additive exPlanations) to provide human-readable reasoning for every critical alert.
*   **Rich Desktop UI:** A fully asynchronous PyQt6 GUI featuring live traffic metrics, attack distribution charts, and severity breakdowns.

---

## 🛠️ Prerequisites

*   **Operating System:** Linux (Debian/Ubuntu, Kali, etc.) recommended for raw socket packet sniffing.
*   **Python:** Python 3.10 or 3.11
*   **Permissions:** `sudo` (root) access is required for the packet sniffer to capture live network traffic.

---

## 📦 Installation

1. **Clone the Repository**
   ```bash
   git clone git@github.com:forgexii/A3-ENDS.git
   cd A3-ENDS
   ```

2. **Create a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🏃‍♂️ Usage Guide

To run the full A3-ENDS suite, you need to start three separate components. It is recommended to open three separate terminal windows.

### 1. Start the Backend Orchestration API
The FastAPI backend acts as the central brain, handling database storage, ML inference orchestration, and serving data to the UI.
```bash
# Terminal 1
cd A3-ENDS
source venv/bin/activate
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 2. Start the Real-Time Network Sniffer
The sniffer captures live traffic from your machine's default network interface and forwards the extracted flow features to the backend. **(Requires Root)**
```bash
# Terminal 2
cd A3-ENDS
source venv/bin/activate
sudo python realtime/runner.py
```
*(Note: If you run this without `sudo`, it will fall back to a simulated traffic generator for development purposes).*

### 3. Launch the Desktop Analyst Dashboard
The PyQt6 dashboard provides the visual interface for the SOC analyst to monitor the network and approve/reject Reinforcement Learning alerts.
```bash
# Terminal 3
cd A3-ENDS
source venv/bin/activate
python a3ends-desktop/main.py
```

---

## 📂 Project Structure

*   `a3ends-desktop/` - PyQt6 frontend desktop application and UI components.
*   `backend/` - FastAPI orchestration server, SQLite database models, and API routes.
*   `datasets/` - Directory for storing the CICIDS2017 training datasets.
*   `models/` - Serialized `.pkl` files for the trained Machine Learning models (XGBoost, Autoencoder).
*   `realtime/` - The core NIDS engine (Packet Capture, Flow Management, Feature Extraction, Risk Engine, RL Agent).
*   `scripts/` - Utilities for training models (`train_realtime_xgboost.py`) and benchmarking algorithms.

---

## 🛡️ Evaluated Threat Detection

The system has been trained and evaluated against the CICIDS2017 dataset to detect the following attack vectors:
*   **DoS / DDoS** (Hulk, GoldenEye, Slowloris, Slowhttptest)
*   **Brute Force** (FTP-Patator, SSH-Patator)
*   **Web Attacks** (XSS, SQL Injection, Brute Force)
*   **Infiltration & Botnets**
*   **Port Scans** (Nmap, stealth SYN probes)
