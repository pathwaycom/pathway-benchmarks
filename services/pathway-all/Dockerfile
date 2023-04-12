FROM python:3.10
# FROM pathway-debug
WORKDIR /pathway-all

ENV USING_BENCHMARK_HARNESS=1

COPY ./requirements.txt /pathway-all/requirements.txt
# ENV PATHWAY_PROFILE=dev
# ENV RUST_BACKTRACE=1
RUN pip install --no-cache-dir --upgrade -r /pathway-all/requirements.txt --extra-index-url https://packages.pathway.com/966431ef6b933cbab9baf6332a9b79e50e4e3c6e42c5a6e6d3fd3767ad31aa2fe443c18312
# RUN pip install --no-cache-dir --upgrade py-spy
COPY ./main.py /pathway-all/main.py
# CMD python main.py --type $BENCHMARK_TYPE --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS
# CMD py-spy --version
CMD pathway spawn --threads $CORES python main.py --type $BENCHMARK_TYPE --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS