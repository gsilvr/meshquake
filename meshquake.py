import requests
import time
import sqlite3
import subprocess
import sys
import logging
from datetime import datetime
import pytz
from math import radians, cos, sin, asin, sqrt
import os

# Config defaults
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "earthquakes.db")
LOG_FILE = os.path.join(DATA_DIR, "meshquake_error.log")
USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
DEFAULT_MODE = "prod"
DEFAULT_MIN_MAGNITUDE = 0.0
DEFAULT_ZIP = None
DEFAULT_MAX_DISTANCE_MILES = 120
LOCATION_LABEL = "SJ"
TABLE_NAME = "processed_quakes"

# --------------------- Logging Setup ---------------------

def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# --------------------- SQLite Setup ---------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id TEXT PRIMARY KEY,
            message TEXT,
            timestamp INTEGER
        )
    """)
    conn.commit()
    conn.close()
    logging.info(f"Initialized DB table: {TABLE_NAME}")

def is_quake_processed(quake_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT 1 FROM {TABLE_NAME} WHERE id = ?", (quake_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_quake_processed(quake_id, message, timestamp):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"INSERT OR IGNORE INTO {TABLE_NAME} (id, message, timestamp) VALUES (?, ?, ?)",
              (quake_id, message, timestamp))
    conn.commit()
    conn.close()
    logging.info(f"Stored in DB: {quake_id}")

def fetch_all_messages():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT id, message, timestamp FROM {TABLE_NAME} ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# --------------------- Distance & Geo ---------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def is_within_radius(lat, lon, center_lat, center_lon, radius):
    return haversine(lat, lon, center_lat, center_lon) <= radius

def lookup_zip(zip_code):
    try:
        url = f"https://api.zippopotam.us/us/{zip_code}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        lat = float(data["places"][0]["latitude"])
        lon = float(data["places"][0]["longitude"])
        city = data["places"][0]["place name"]
        return lat, lon, city
    except Exception as e:
        logging.error(f"ZIP code lookup failed: {e}")
        print(f"[ERROR] ZIP code lookup failed: {e}")
        sys.exit(1)

# --------------------- Data Fetch ---------------------

def fetch_earthquake_data():
    try:
        response = requests.get(USGS_FEED_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Fetch error: {e}")
        return None

# --------------------- CLI Message Send ---------------------

def send_meshtastic_message(text, target_ip=None, channel=0):
    cmd = ["meshtastic"]
    if target_ip:
        cmd.extend(["-t", target_ip])
    cmd.extend(["--ch-index", str(channel), "--sendtext", text])
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Sent message (ch {channel}): {text}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Meshtastic send failed: {e}")
        logging.error(f"Failed message: {text}")

# --------------------- Main Processing ---------------------

def process_earthquakes(data, mode="prod", radio_ip=None, min_mag=0.0, channel=0, center_lat=None, center_lon=None, max_distance=120):
    if not data or "features" not in data:
        logging.info("No data returned or missing 'features'")
        return

    sorted_quakes = sorted(data["features"], key=lambda f: f["properties"].get("time", 0), reverse=True)

    for feature in sorted_quakes:
        quake_id = feature["id"]
        if mode == "prod" and is_quake_processed(quake_id):
            continue

        properties = feature["properties"]
        geometry = feature["geometry"]
        if not geometry or "coordinates" not in geometry:
            continue

        lon, lat, depth = geometry["coordinates"]
        if not is_within_radius(lat, lon, center_lat, center_lon, radius=max_distance):
            continue

        magnitude = properties.get("mag", 0)
        if magnitude < min_mag:
            continue

        place = properties.get("place", "Unknown location")
        time_epoch = properties.get("time", 0) / 1000
        short_date = datetime.fromtimestamp(time_epoch, pytz.timezone("America/Los_Angeles")).strftime("%m-%d %H:%M")
        distance = haversine(lat, lon, center_lat, center_lon)

        part1 = f"M{magnitude:.1f} {distance:.0f}mi from {LOCATION_LABEL}"
        part2 = place
        part3 = f"{short_date} PDT"
        full_message = f"{part1}: {part2}, {part3}"
        message_bytes = len(full_message.encode("utf-8"))

        logging.info(f"Matched quake: {quake_id} -> {full_message}")
        mark_quake_processed(quake_id, full_message, int(time_epoch))

        if mode == "dev":
            print("[DEV MODE]")
            print("Most recent matching message (not sent):")
            print(full_message)
            print("\nAll simulated stored messages (dev table):\n")
            rows = fetch_all_messages()
            for r in rows:
                ts = datetime.fromtimestamp(r[2])
                print(f"{ts} | {r[1]}")
            return

        if message_bytes <= 200:
            send_meshtastic_message(full_message, target_ip=radio_ip, channel=channel)
        else:
            send_meshtastic_message(f"Part 1: {part1}", target_ip=radio_ip, channel=channel)
            time.sleep(4)
            send_meshtastic_message(f"Part 2: {part2}", target_ip=radio_ip, channel=channel)
            time.sleep(4)
            send_meshtastic_message(f"Part 3: {part3}", target_ip=radio_ip, channel=channel)

        return  # Send/store one quake per run

# --------------------- Argument Parser ---------------------

def parse_args():
    mode = DEFAULT_MODE
    radio_ip = None
    zip_code = DEFAULT_ZIP
    min_mag = DEFAULT_MIN_MAGNITUDE
    channel = 0
    max_distance = DEFAULT_MAX_DISTANCE_MILES

    args = sys.argv[1:]
    if len(args) > 0 and args[0] in ["dev", "prod", "devsend"]:
        mode = args[0].lower()

    if "--radio-ip" in args:
        radio_ip = args[args.index("--radio-ip") + 1]

    if "--zip" in args:
        zip_code = args[args.index("--zip") + 1]

    if "--min-mag" in args:
        try:
            min_mag = float(args[args.index("--min-mag") + 1])
        except (IndexError, ValueError):
            print("Usage: --min-mag <float>")
            sys.exit(1)

    if "--ch-index" in args:
        try:
            channel = int(args[args.index("--ch-index") + 1])
        except (IndexError, ValueError):
            print("Usage: --ch-index <int>")
            sys.exit(1)

    if "--max-distance" in args:
        try:
            max_distance = float(args[args.index("--max-distance") + 1])
        except (IndexError, ValueError):
            print("Usage: --max-distance <float>")
            sys.exit(1)

    return mode, radio_ip, zip_code, min_mag, channel, max_distance

# --------------------- Main ---------------------

def main():
    setup_logging()
    mode, radio_ip, zip_code, min_mag, channel, max_distance = parse_args()
    logging.info(f"Mode: {mode}, ZIP: {zip_code}, MinMag: {min_mag}, MaxDist: {max_distance}, RadioIP: {radio_ip}, Channel: {channel}")

    global TABLE_NAME
    TABLE_NAME = "processed_quakes_dev" if mode in ["dev", "devsend"] else "processed_quakes"

    init_db()

    lat, lon = 37.3382, -121.8863  # default San Jose
    global LOCATION_LABEL

    if zip_code:
        lat, lon, city = lookup_zip(zip_code)
        LOCATION_LABEL = city
        logging.info(f"Resolved location: {LOCATION_LABEL} @ ({lat}, {lon})")

    if mode not in ["dev", "prod", "devsend"]:
        print("Usage: python3 meshquake.py [dev|prod|devsend] [--radio-ip <ip>] [--zip <zipcode>] [--min-mag <value>] [--ch-index <int>] [--max-distance <miles>]")
        return

    if mode == "dev":
        data = fetch_earthquake_data()
        process_earthquakes(data, mode="dev", radio_ip=radio_ip, min_mag=min_mag, channel=channel, center_lat=lat, center_lon=lon, max_distance=max_distance)

    elif mode == "devsend":
        data = fetch_earthquake_data()
        process_earthquakes(data, mode="devsend", radio_ip=radio_ip, min_mag=min_mag, channel=channel, center_lat=lat, center_lon=lon, max_distance=max_distance)

    elif mode == "prod":
        while True:
            data = fetch_earthquake_data()
            process_earthquakes(data, mode="prod", radio_ip=radio_ip, min_mag=min_mag, channel=channel, center_lat=lat, center_lon=lon, max_distance=max_distance)
            time.sleep(60)

if __name__ == "__main__":
    main()
