# 🗺️ ResQRoute AI

### Autonomous, Data-Driven Transit & Agentic Intervention Engine for Perishable Logistics

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-v1.30+-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Submission Quick Links

* **🎥 3-Minute Demo Video:** 
* **🌐 Live Interactive Dashboard:** [ResQRoute AI Live Streamlit App](https://resqroute-ai-hflgqptoacqdppt7cziobq.streamlit.app)
* **🛠️ Core Repo:** [https://github.com/Hackatona8/resqroute-ai](https://github.com/Hackatona8/resqroute-ai)

---

## 📖 Project Overview

Global supply chains lose over one-third of all perishable food during transit due to systemic delays and cold-chain failures. **ResQRoute AI** turns passive fleet tracking into an active, autonomous salvage operation. 

Instead of treating a cargo temperature spike as a lost cause, ResQRoute AI ingests simulated IoT telemetry, calculates dynamic spoilage risk, instantly reroutes vehicles using real-time traffic/thermal graphs, and triggers AI agents to offload stock to alternative micro-hubs via smart-markdown pricing models before the food spoils.

---

## 🛠️ Core Engineering Features

ResQRoute AI is engineered from the ground up to showcase **technical depth and multi-disciplinary systems integration**:

* **🚀 High-Throughput Ingestion (FastAPI):** Asynchronous API layer hosting robust Pydantic data contract models capable of receiving high-frequency telemetry packets from thousands of active fleet vehicles.
* **📈 Cumulative Spoilage Math (Pandas Engine):** A heavy-duty data analytics layer that models real-world thermodynamic decay. Rather than relying on simple static thresholds, it uses rolling vector matrices to evaluate risk based on ambient temperatures, cargo vulnerabilities, and duration of thermal exposure.
* **🚦 Dynamic Alternative Routing (NetworkX Graph Engine):** Uses customized **A* Search Algorithms** on dynamic edge-weighted geographic graphs. When a vehicle's cargo enters a critical threshold, edges are re-weighted, and a fast path is instantly recalculated to the nearest viable micro-hub.
* **🤖 Autonomous Liquid-Market Valuation (LangChain Layer):** A deterministic, structured agent layer that takes over the moment a reroute happens. It evaluates the degradation level, calculates an optimal dynamic discount matrix (e.g., -40%), maps it to an authorized local buyer ID, and packages a validated JSON payload ready for downstream webhook execution.
* **🖥️ Glassmorphism Command Center UI (Streamlit & Folium):** A reactive dashboard that bridges the entire stack. Features manual telemetry injection tools, live map route drawing (**Blue** for nominal transit, switching instantly to **Red** for critical salvage pathing), and an interactive terminal console displaying the active AI agent's decision logs.

---

## 🏗️ System Architecture

~~~text
 [ IoT Telemetry Injection ]
            │
            ▼
┌────────────────────────────────────────┐
│      FastAPI Ingestion Backend         │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│      Pandas Thermodynamic Engine       │ -> Calculates Rolling Spoilage Risk
└───────────────────┬────────────────────┘
                    │ (If Risk Score > 72%)
                    ▼
┌────────────────────────────────────────┐
│     NetworkX Graph Routing Engine      │ -> Dynamic A* Alternative Pathing
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│     LangChain Autonomous Agent         │ -> Emits Structured Discount JSON
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│   Streamlit Command Center Frontend    │ -> Real-time Folium Map Visualization
└────────────────────────────────────────┘
~~~

---

## 💻 Technical Stack

* **Language:** Python 3.11+
* **Frameworks & API:** FastAPI, Uvicorn, Pydantic
* **Data Processing & Analytics:** Pandas, NumPy
* **Graph Algorithms:** NetworkX
* **Agentic Framework:** LangChain / Structured JSON Output Layer
* **Frontend Visualization:** Streamlit, Folium, Streamlit-Folium
* **Quality Assurance:** Pytest

---

## 🚀 Quick Start Guide

### 1. Installation & Environment Configuration
Clone the repository and set up your local development environment:

~~~bash
# Clone the repository
git clone https://github.com/Hackatona8/resqroute-ai.git
cd resqroute-ai

# Set up local dependencies
python -m pip install -r requirements.txt
~~~

### 2. Launch the FastAPI Core Engine
Start the background ingestion server and computational pipeline:

~~~bash
python -m src.main
~~~
*The API will actively listen on `http://localhost:8000` with interactive Swagger docs accessible at `/docs`.*

### 3. Launch the Fleet Command Center
In a separate terminal tab, spin up the visual frontend layer:

~~~bash
python -m streamlit run src/frontend/app.py
~~~
*The command center interface will automatically boot in your browser at `http://localhost:8501`.*

---

## 🧪 Verification & Testing Suite

We maintain strict test-driven development metrics. Run the automated test suite to validate API contracts, route mutations, and agent generation pipelines:

~~~bash
python -m pytest
~~~

---

## 👥 Engineering & Leadership Team

* **Piyush Goel** — Public Relations Head, IEEE BVICAM Student Branch | MCA Candidate, BVICAM & BS Degree Scholar, IIT Madras
* **Divyansh Jha** — Software Engineer at SAP Labs Bangalore | Mtech BITS Pilani

> *Built Boldly. Shipped for FAR AWAY Hackathon 2026.*