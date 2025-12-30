# Meshquake (Docker Edition)

Meshquake monitors real-time earthquakes via USGS and sends alerts over Meshtastic mesh radios.

---

## 🔧 What It Does

- Polls the USGS real-time earthquake feed
- Filters quakes by:
  - ZIP code location
  - Radius (in miles)
  - Minimum magnitude
- Sends formatted messages with emojis via Meshtastic CLI
- Announces initialization on startup with monitoring parameters
- Stores quake history in SQLite
- Logs activity and errors
- Fully containerized with Docker + Compose
- Persistent logs and DB outside container

---

## 🚀 Deployment

### Prerequisites

- Docker
- Docker Compose

### Clone and Run

```bash
git clone https://github.com/gsilvr/meshquake.git
cd meshquake
mkdir -p data
docker-compose build
docker-compose up -d
```

This will:

- Build the container
- Persist logs and DB to `./data/`
- Run in `prod` mode with default flags (see below)
- Send an initialization message to the mesh on startup
- You will need to wait for a quake to actually happen in order to see if it's working

---

## ⚙️ Configuration

Edit `docker-compose.yml` to change runtime flags.

Example:

```yaml
command: >
  prod --zip 95014 --min-mag 1.0 --max-distance 100
  --radio-ip 192.168.69.211 --ch-index 1
```

---

## 🔁 Runtime Modes

| Mode       | Description                                      |
|------------|--------------------------------------------------|
| `dev`      | Dry run, log only                                |
| `devsend`  | Sends to test radio, logs to separate dev table  |
| `prod`     | Full runtime, persistent logging + DB            |

---

## 🧾 Flags

| Flag             | Description                                |
|------------------|--------------------------------------------|
| `--zip`          | ZIP code for center location (required)    |
| `--min-mag`      | Minimum quake magnitude (e.g. `1.5`)       |
| `--max-distance` | Max radius in miles (default: 120)         |
| `--radio-ip`     | Target Meshtastic node IP                  |
| `--ch-index`     | Channel index for sending (default: 0)     |

---

## 🗃 Persistent Output

All output is stored in the `./data` directory:

- `meshquake_error.log` — logs
- `earthquakes.db` — SQLite DB of quake events

---

## 📤 Example Output

### Initialization Message

On startup (in `prod` and `devsend` modes), meshquake sends:

```
🌎 Meshquake initialized! 📡
Monitoring near Mt View
M1.0+ | 120mi
```

### Earthquake Alerts

Earthquake alerts are formatted with emojis and multi-line formatting:

```
🌎 Earthquake Alert!
📍 M2.3 | 88mi from Mt View
🗺️ 3 km W of Cobb, CA
⏰ 05-21 22:01 PDT
```

Long messages (>200 bytes) are automatically chunked into separate messages:

```
🌎 Earthquake Alert!
📍 M2.3 | 88mi from Mt View
```

```
🗺️ 3 km W of Cobb, CA
```

```
⏰ 05-21 22:01 PDT
```

---

## 🧹 Reset State

To clear logs and DB:

```bash
rm -f data/earthquakes.db data/meshquake_error.log
```

---

## 🛑 Stop the Service

```bash
docker-compose down
```

---

## 🛠 Maintenance Notes

- Logs rotate manually (watch file size)
- DB stores quake IDs to avoid duplicates
- `prod` polls every 60 seconds
- All files persist under `./data/`

---

## ✅ Status

Stable • Dockerized • Ready for unattended use
