# Pathway side of the MySQL bulk-write benchmark.
#
# Installs the latest (nightly) Pathway Live Data Framework from the Pathway
# package index — no local build.
FROM python:3.11

RUN pip install --pre --no-cache-dir --upgrade pathway \
    --extra-index-url https://packages.pathway.com/966431ef6b933cbab9baf6332a9b79e50e4e3c6e42c5a6e6d3fd3767ad31aa2fe443c18312

COPY main.py /app/main.py
WORKDIR /app

CMD ["python", "main.py"]
