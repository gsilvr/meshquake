#!/bin/bash
set -e

# Write crontab with env vars baked in
echo "0 */12 * * * RADIO_IP=${RADIO_IP} CH_INDEX=${CH_INDEX} /app/send_test_message.sh" | crontab -

# Start cron in the background
cron

# Launch the main app as PID 1
exec conda run -n meshquake python meshquake.py "$@"
