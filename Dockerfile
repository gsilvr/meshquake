FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Copy app files
COPY environment.yml .
COPY meshquake.py .
COPY entrypoint.sh .
COPY send_test_message.sh .
RUN chmod +x entrypoint.sh send_test_message.sh

# --- TIMEZONE FIX ---
ENV TZ=America/Los_Angeles
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata cron && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*
# ---------------------

# Create conda environment
RUN conda env create -f environment.yml

# Ensure conda runs bash with the correct env
SHELL ["conda", "run", "-n", "meshquake", "/bin/bash", "-c"]

# Meshquake data dir
ENV DATA_DIR=/app/data

# Run the app in LA time
ENTRYPOINT ["/app/entrypoint.sh"]