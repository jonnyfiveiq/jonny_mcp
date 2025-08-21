# Ansible Automation Platform MCP Server

This project provides a **Model Context Protocol (MCP) server** for interacting with **Ansible Automation Platform (AAP)** through Claude or other MCP-aware clients.  
It allows you to chat with Claude and run AAP operations (e.g. ping the controller, list jobs, create/run job templates).

---

## Features

- MCP server written in Python (`server.py`)
- Connects to your AAP instance via REST API
- Loads credentials from `.env`
- Provides tools such as:
  - `ping_aap` – check connectivity to your AAP controller
  - (extensible) list jobs, launch job templates, etc.

---

## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (recommended for venv management)
- [Claude desktop app](https://claude.ai) with MCP support

---

## Setup

1. Clone this repo:

   ```bash
   git clone https://github.com/yourname/aap-mcp-server.git
   cd aap-mcp-server
