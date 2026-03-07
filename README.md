# SafeLAN — README

## Installation

### Environment Setup

The application requires **Python 3.11**. It is highly recommended to use separate virtual environments to avoid library conflicts between the ML-heavy server and the vision-heavy client.

---

### 1. Server Installation
```bash
cd Server
python -m venv serverVENV
.\serverVENV\Scripts\activate
pip install -r requirements.txt
```

### 2. Client Installation

Navigate to the client directory to install the GUI and computer vision components.
```bash
cd Client
python -m venv clientVENV
.\clientVENV\Scripts\activate
pip install -r requirements.txt
```

---

## Execution

For the system to function, the **Server must be running first** so the Client can establish a connection for authentication.

### 1. Starting the Server

From the `Server` directory with the virtual environment active:
```bash
python run_server.py
```

### 2. Starting the Client
```bash
python -m Client.src.gui.app
```

---

## Configuration

### 1. Accessing Settings

From the Sidebar (available after login or via the initialization screen), select **Settings**.

### 2. Input Entry

| Field | Description |
|---|---|
| **Server IP Address** | The IPv4 address where the SafeLAN Server is hosted (e.g., `127.0.0.1` for local testing) |
| **Communication Port** | The port number assigned to the FastAPI server (default: `8000`) |

### 3. Applying Changes

Clicking **Update Gateway** triggers the following background actions:

- **Persistence** — The new IP and port are saved to the local configuration file via `save_server_config`.
- **Global Broadcast** — The `SafeLANApp` controller calls `update_api_base()`, which updates the endpoint for the `AuthEngine` and all GUI frames.
- **Health Check** — A background thread pings the `{url}/health` endpoint. If successful, the status indicator turns green (● Connection Active); otherwise, it displays a red warning.
