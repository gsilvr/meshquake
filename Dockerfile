FROM continuumio/miniconda3

WORKDIR /app

COPY environment.yml .
COPY meshquake.py .

RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "meshquake", "/bin/bash", "-c"]

ENV DATA_DIR=/app/data

ENTRYPOINT ["conda", "run", "-n", "meshquake", "python", "meshquake.py"]
