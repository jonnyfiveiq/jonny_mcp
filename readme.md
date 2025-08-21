# UNOFFICIAL Ansible Automation Platform MCP Server

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


2. Create a virtual environment and install dependencies

uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

3. Create .env file

AAP_BASE_URL=https://192.168.0.174
AAP_USERNAME=admin
AAP_PASSWORD=********
AAP_VERIFY_SSL=true
AAP_TIMEOUT_SEC=30

4. Run in MCP Inspector (for debugging)

mcp dev server.py

5. Integrate with Claude
Open the Claude Desktop App.
Go to Settings → Developer → Local MCP servers.
Click Edit Config and add your server:

{
  "aap": {
    "command": "uv",
    "args": [
      "run",
      "server.py"
    ],
    "env": {
      "AAP_BASE_URL": "https://192.168.0.174",
      "AAP_USERNAME": "admin",
      "AAP_PASSWORD": "********"
    }
  }
}


## Using the Server in Claude
Once connected, you can ask Claude to use your MCP server directly in chat. Examples:

Ping AAP

Use the aap server and run ping_aap. 
or simply:
ping_aap

- List available tools
- What tools does the aap server provide?
- Run a job (after adding more tools)
- Launch job template 42 in AAP.
- Check jobs
- List the most recent jobs in Ansible Automation Platform.
