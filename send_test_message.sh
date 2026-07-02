#!/bin/bash
# Invoked by cron, which runs with a minimal PATH that does NOT include conda.
# Call the meshtastic binary from the conda env by absolute path instead of `conda run`.
MESHTASTIC=/opt/conda/envs/meshquake/bin/meshtastic
"${MESHTASTIC}" --host "${RADIO_IP}" --ch-index "${CH_INDEX}" --sendtext "Meshquake Heartbeat - https://bayme.sh/ Discord for any questions" >> /app/data/meshquake_error.log 2>&1
