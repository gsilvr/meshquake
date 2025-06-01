# Meshquake

**Meshquake** is a Python script that monitors recent earthquakes from the USGS and sends nearby quake alerts over Meshtastic mesh radios.

---

## 🔧 What It Does

- Polls the USGS real-time earthquake feed
- Filters quakes by:
  - Location (via ZIP code)
  - Radius (miles from center)
  - Minimum magnitude
- Formats messages for delivery
- Sends messages to Meshtastic devices via CLI
- Logs and stores quake history using SQLite

---

## 📦 Installation Instructions

### 1. Install [Conda](https://docs.conda.io/en/latest/miniconda.html)

Meshquake runs best in a clean Conda environment.

---

### 2. Clone the repository

```bash
git clone https://github.com/gsilvr/meshquake.git
cd meshquake
```

---

### 3. Create the environment

Create a Conda environment using this minimal `environment.yml` file:

```yaml
name: meshquake
channels:
  - defaults
dependencies:
  - python=3.10
  - requests
  - pytz
  - pip
  - pip:
      - meshtastic
```

Then create and activate it:

```bash
conda env create -f environment.yml
conda activate meshquake
```

---

## ⚙️ Configuration Overview

All configuration is done via command-line flags — no config files needed.

- Earthquake data: USGS GeoJSON feed (no API key required)
- Location filtering: Based on ZIP code and max distance
- Message delivery: Meshtastic CLI (`meshtastic --sendtext`)
- Logging: `meshquake_error.log`
- Database: SQLite (`earthquakes.db`)

---

## 🚀 Usage

```bash
python3 meshquake.py [mode] [flags]
```

---

### 🧪 Modes

| Mode       | Description                                                                 |
|------------|-----------------------------------------------------------------------------|
| `dev`      | Dry run — shows what would be sent, logs but does not transmit             |
| `devsend`  | Sends messages to your test radio, but logs to a separate dev DB           |
| `prod`     | Production mode — runs continuously, sends real messages, logs permanently |

---

### 🛠 Available Flags

| Flag              | Description                                              |
|-------------------|----------------------------------------------------------|
| `--zip`           | ZIP code to use as center location (required)           |
| `--min-mag`       | Minimum earthquake magnitude (e.g. `--min-mag 1.5`)      |
| `--max-distance`  | Maximum distance (in miles) from center (default: 120)   |
| `--radio-ip`      | IP of the target Meshtastic node (e.g. `192.168.69.211`) |
| `--ch-index`      | Meshtastic channel index (default: `0`)                  |

---

## ✅ Examples

### Show upcoming message (dry run)

```bash
python3 meshquake.py dev --zip 95014 --min-mag 1.0
```

---

### Send to a dev radio (but don't write to prod DB)

```bash
python3 meshquake.py devsend --zip 95014 --min-mag 1.0 --radio-ip 192.168.69.211 --ch-index 1
```

---

### Full production run

```bash
python3 meshquake.py prod --zip 95014 --min-mag 1.0 --max-distance 100 --radio-ip 192.168.69.211 --ch-index 1
```

Runs indefinitely, polling the USGS every 60 seconds.

---

### Running with `cron` (every minute)

```cron
* * * * * /path/to/conda/envs/meshquake/bin/python /path/to/meshquake/meshquake.py prod --zip 95014 --min-mag 1.0 --radio-ip 192.168.69.211 --ch-index 1 --max-distance 100 >> /dev/null 2>&1
```

---

## 📂 Output Files

| File                 | Purpose                            |
|----------------------|------------------------------------|
| `meshquake_error.log`| All logs (INFO, ERROR)             |
| `earthquakes.db`     | SQLite DB of processed quake events|
| `processed_quakes_dev` | Separate table used for dev modes |

---

## 📨 Example Output

```text
M2.3 88mi from Cupertino: 3 km W of Cobb, CA, 05-21 22:01 PDT
```

If over 200 bytes, it's chunked like this:

```text
Part 1: M2.3 88mi from Cupertino
Part 2: 3 km W of Cobb, CA
Part 3: 05-21 22:01 PDT
```

---

## 🔁 Reset / Cleanup

To reset DB and logs:

```bash
rm earthquakes.db meshquake_error.log
```

---

## 🧰 Dependencies

| Package     | Purpose              |
|-------------|----------------------|
| `requests`  | USGS + ZIP API calls |
| `pytz`      | Timezone formatting  |
| `meshtastic`| Mesh radio CLI       |

Install with:

```bash
conda install requests pytz pip
pip install meshtastic
```

Or use the provided `environment.yml`.

---

## 🧼 Maintenance

- Logs rotate manually — monitor `meshquake_error.log` size
- DB stores quake IDs to prevent repeat alerts
- `dev` and `devsend` modes are safe for testing

---

## ✅ Status

Stable • Ready for real-world deployment
