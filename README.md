# Cockpit-Jupyter-LLM-VPS

A comprehensive project combining server management, LLM experimentation, and **multiple lightweight evolving agents** running on a VPS.

## Features

* **Cockpit Integration**
  Web-based server management (requires `systemd`)

* **Jupyter + LLM Notebooks**
  Interactive experimentation with Large Language Models

* **Multi-Agent Virtual Assistant System**

  * Phone call handling via **Twilio**
  * Local LLM inference via **Ollama**
  * Persistent self-learning agents

---

## Agent Lineup

### 1. **Primary Assistant Agent**

* Conversational interface
* Learns from user interactions
* Stores lessons in JSON memory
* Evolves prompt behavior over time

Implemented by:

* `agent.py`
* `runner.py`
* `nano_agent.py` (ultra-minimal)

---

### 2. **📞 Telephony Agent (Twilio)**

* Handles inbound/outbound calls
* Can route calls to LLM reasoning
* Designed to plug into the Primary Agent for responses

> Integration point only — logic depends on Twilio webhook setup

---

### 3. **System Observer Agent (NEW)**

A **dedicated background agent** focused on **system awareness and orchestration**.

#### Purpose

* Monitors system state (CPU, memory, disk, services)
* Feeds operational insights to other agents
* Acts as a “silent observer” rather than a conversational bot

### Responsibilities

* Periodic self-checks
* Lightweight reflections (“system under load”, “model slow”, etc.)
* Writes insights into shared memory for other agents to consume

---

## Architecture Overview

```
┌────────────────────┐
│ Cockpit (Web UI)   │
└─────────┬──────────┘
          │
┌─────────▼──────────┐
│ VPS / systemd      │
├────────────────────┤
│ Ollama (LLMs)      │
│ Jupyter Notebooks  │
├────────────────────┤
│ Agent Mesh         │
│  - Primary Agent   │
│  - Twilio Agent    │
│  - System Observer Agent │
└────────────────────┘
```

---

## Key Benefits (Updated)

1. **Multi-agent design** (conversation + ops + telephony)
2. **Ultra-lightweight** (1–3B models, stdlib only)
3. **Self-learning & persistent**
4. **VPS-friendly**
5. **Composable & Docker-ready**
