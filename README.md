# KNAV - Kerbal Navigation and Autopilot

A comprehensive control system for Kerbal Space Program (KSP) that automates various spaceflight operations using kRPC. This project aims to provide a robust and reliable automation system for various spacecraft operations in KSP.

## Features

- 🚀 Automated Launch System
  - Gravity Turn Optimization
  - Stage Management
  - Fuel Monitoring
- 🛰️ Orbital Maneuvers
  - Circularization


## Prerequisites

- Kerbal Space Program (Latest Version)
- kRPC Mod
- Python 3.8 or higher
- Required Python packages (see `requirements.txt`)

## Installation

1. Install KSP and the kRPC mod
2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/kos.git
   cd kos
   ```
3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start KSP and load your save game
2. Ensure kRPC server is running in KSP
3. Run the main control script:
   ```bash
   python main.py
   ```

## Project Structure

```
kos/
├── core/
│   ├── launch/         # Launch sequence automation
│   │   └── gravity_turn.py
│   ├── orbital/        # Orbital maneuvers
│   ├── docking/        # Docking operations
│   ├── telemetry/      # Data collection and monitoring
│   └── utils/          # Utility functions
├── docs/              # Documentation
│   └── RESOURCES.md   # kRPC resource documentation
└── main.py           # Main entry point
```

## Features in Detail

### Launch System
- Automated gravity turn with optimized ascent profile
- Real-time fuel monitoring and stage management
- Dynamic pitch control based on flight conditions
- Automatic stage separation when fuel is depleted

### Telemetry System
- Color-coded logging with timestamps
- Mission status tracking
- Real-time resource monitoring
- Formatted telemetry data display
