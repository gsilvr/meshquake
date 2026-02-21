#!/bin/bash
conda run -n meshquake meshtastic --host "${RADIO_IP}" --ch-index "${CH_INDEX}" --sendtext "Meshquake Test - https://bayme.sh/ Discord for any questions" >> /app/data/meshquake_error.log 2>&1
