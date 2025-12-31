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

---

## 🏗️ Technical Architecture

The project is built with a modular, factory-based architecture designed for production and easy scaling.

### Core Stack

* **FastAPI**: High-performance API layer with Pydantic validation.
* **LangChain**: Open-source framework for agentic workflows and tool use.
* **Ollama**: Local-first LLM inference (`qwen2.5`, `phi-2`, `tinyllama`).
* **Resemble.AI**: Advanced voice synthesis and cloning.

### Project Structure

```
cockpit-jupyter-llm-vps/
├── api/              # FastAPI app, routes, and logic
├── agents/           # Modular Agent implementations (LangChain, Ollama)
├── assistant/        # Core cognitive modules (Ethics, Debate, Goals)
├── config/           # Pydantic-settings and constants
├── memory/           # Conversation and long-term storage
├── scripts/          # Automation and setup scripts
├── Dockerfile        # Production Docker build
└── render.yaml       # Render deployment configuration
```

---

## 🛠️ Stack Components

* **Unified Agent Factory**: Dynamically switch between standard LangChain tools and custom cognitive stacks.
* **Enhanced Tools**: Integrated Shell, Web Search, and Crypto Price checks.
* **"Almost Human" Swarm**: Multi-agent reasoning with internal debate and ethical filtering.
* **Production Ready**: Optimized for Render, containing health checks and structured logging.

---

---

## 🌐 Web UI & Voice Interaction

The project now includes **Open WebUI** for a premium browser-based experience.

### Accessing the UI

* **Open WebUI**: `http://localhost:3001`
* **First Login**: Create a local account (all data stays on your machine).
* **Model Selection**: Select `trinity-core-agent` from the dropdown.

### 🎙️ Talking to Your Agent

1. Click the **Microphone Icon** in the chat bar to enable browser-based Speech-to-Text.
2. Go to **Settings > Audio** to enable Text-to-Speech (Output).
3. For the best experience, choose "Browser Speech Engine" or plug in your local Piper/Whisper endpoints.

### 🧠 How it Works

We use a FastAPI middleware (`api/agent_server.py`) that acts as an OpenAI-compatible bridge. This allows Open WebUI to talk directly to our **Almost Human** cognitive stack instead of raw Ollama.

---

## 🚀 Quick Start (Web UI)

1. **Pull Required Models**:

   ```bash
   ollama pull qwen2.5:7b
   ollama pull phi-2
   ollama pull tinyllama
   ```

2. **Start the Swarm**:

   ```bash
   docker-compose up -d
   ```

3. **Open the Dashboard**: Visit `http://localhost:3001`.
