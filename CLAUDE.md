# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Meshquake monitors real-time earthquakes from the USGS feed and sends formatted alerts over Meshtastic mesh radio networks. It's a single-file Python application (`meshquake.py`, ~300 lines) designed for unattended Docker deployment on Raspberry Pi.

## Build & Run Commands

```bash
# Build and run
docker-compose build
docker-compose up -d

# View logs
docker logs -f meshquake-meshquake-1

# Reset state (clear DB and logs)
rm -f data/earthquakes.db data/meshquake_error.log

# Verify cron is running
docker exec meshquake-meshquake-1 crontab -l

# Manually trigger test message
docker exec meshquake-meshquake-1 /app/send_test_message.sh
```

There are no unit tests, linters, or formatters configured.

## Architecture

**Single-file app** — all logic lives in `meshquake.py`. No packages, no modules.

### Runtime Modes (first CLI arg)
- `dev` — dry run, no message sending, uses `processed_quakes_dev` table
- `devsend` — sends to radio but uses dev table
- `prod` — continuous 60-second polling loop, sends alerts, uses `processed_quakes` table

### Data Flow
1. `parse_args()` → manual `sys.argv` parsing (no argparse)
2. `lookup_zip()` → resolves ZIP to lat/lon/city via zippopotam.us API
3. `fetch_earthquake_data()` → polls USGS GeoJSON feed (all quakes, last hour)
4. `process_earthquakes()` → filters by Haversine distance and magnitude, formats message, sends via Meshtastic CLI
5. Only processes **one quake per polling cycle** (returns after first match)

### Meshtastic Integration
Messages are sent by shelling out to the `meshtastic` CLI tool via `subprocess.run()`. Messages >200 bytes are chunked into 3 parts with 4-second delays between sends.

### Persistence
- SQLite database (`data/earthquakes.db`) tracks processed quake IDs to prevent duplicate alerts
- Error log at `data/meshquake_error.log`
- Both persist outside the container via volume mount (`./data:/app/data`)

### Container Setup
- **Dockerfile**: miniconda3 base → conda env from `environment.yml` → cron + tzdata installed
- **entrypoint.sh**: installs cron job (12-hour test messages), starts cron daemon, then `exec`s the Python app as PID 1
- **send_test_message.sh**: cron-triggered script that sends a test message via meshtastic CLI
- `RADIO_IP` and `CH_INDEX` env vars in docker-compose.yml must match the `command:` flags (env vars are used by cron, flags by the Python app)

### Key Globals
- `LOCATION_LABEL` — mutable global, set from ZIP lookup, hardcoded abbreviation for "Mountain View" → "Mt View"
- `TABLE_NAME` — mutable global, switches between prod/dev SQLite tables

## Dependencies (environment.yml)

Python 3.10 via conda: `requests`, `pytz`, `meshtastic` (pip). No dev dependencies.
