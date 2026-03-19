# KNAV Flight Software & Mission Control Center

External flight software and Mission Control Center for Kerbal Space Program, built on the [KRPC](https://krpc.github.io/krpc/) mod. Uses the Guidance-Navigation-Control (GNC) pattern, state machines, and a web-based Mission Control UI.

## Architecture

```
KRPC Server (KSP)
    │ streams
    ▼
┌────────────┐  VesselState   ┌────────────┐  GuidanceCmd   ┌────────────┐
│ NAVIGATION │ ──────────────>│  GUIDANCE   │ ──────────────>│  CONTROL   │
│ Read       │                │ Active      │                │ Throttle   │
│ streams,   │                │ maneuver    │                │ AP/SAS     │
│ build      │                │ compute     │                │ Staging    │
│ state      │                │ guidance()  │                │ Warp       │
└────────────┘                └────────────┘                └─────┬──────┘
                                                                  │ KRPC RPCs
                                                                  ▼
                                                           KRPC Server (KSP)
```

The GNC loop runs at 20 Hz on a dedicated thread. A FastAPI backend serves REST endpoints and WebSocket channels for the React frontend.

### Package Structure

| Package | Purpose |
|---|---|
| `knav/astro/` | Pure orbital mechanics library (no KRPC dependency) |
| `knav/krpc_interface/` | KRPC abstraction layer — connection, streams, scene detection |
| `knav/fsw/` | Flight software — GNC loop, state machines, maneuvers |
| `knav/models/` | Pydantic data models shared by FSW and API |
| `knav/events/` | Thread-safe event bus for cross-thread communication |
| `knav/api/` | FastAPI backend — REST, WebSocket, serves frontend |
| `knav/frontend/` | React + shadcn/ui Mission Control Center |

### Supported Maneuvers

- Gravity turn (atmosphere to orbit)
- Circularization (with correction burns)
- Hohmann transfer (with phase angle timing)
- Bi-elliptic transfer
- Plane change
- Rendezvous & docking
- Deorbit & landing
- Generic maneuver node executor

## Requirements

- Python 3.12+
- KSP with [KRPC mod](https://krpc.github.io/krpc/) installed and running
- Node.js 20+ (for frontend development)

## Setup

```bash
# Install Python dependencies
uv sync

# Copy and configure environment
cp .env.example .env
# Edit .env with your KRPC server address/ports
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `KRPC_ADDRESS` | `192.168.1.82` | KRPC server IP |
| `KRPC_RPC_PORT` | `50000` | KRPC RPC port |
| `KRPC_STREAM_PORT` | `50001` | KRPC stream port |
| `GNC_RATE_HZ` | `20` | GNC loop frequency |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |

See `knav/config.py` for the full configuration reference including gravity turn parameters, node executor thresholds, and maneuver tolerances.

## Testing

```bash
# Pure math tests (no KSP required)
uv run pytest tests/test_astro/

# All unit tests
uv run pytest

# Lint & format
uv run ruff check .
uv run ruff format --check .
```

## Tech Stack

**Backend:** Python 3.12, FastAPI, KRPC, Pydantic, structlog, NumPy

**Frontend:** React, TypeScript, shadcn/ui, Tailwind CSS, Vite, Zustand, Recharts
