FROM python:3.10

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    USING_BENCHMARK_HARNESS=1

RUN apt-get update
WORKDIR /stats-collector

RUN apt-get install -y libsasl2-dev
RUN curl https://sh.rustup.rs -sSf > rust-installer.sh
RUN bash rust-installer.sh -y

COPY ./src /stats-collector/src
COPY ./Cargo.lock /stats-collector/Cargo.lock
COPY ./Cargo.toml /stats-collector/Cargo.toml
RUN cargo build --release

COPY ./main.py /stats-collector/main.py

CMD python main.py --type $BENCHMARK_TYPE --batch-size $COMMIT_FREQUENCY --rate-per-second $RATE_PER_SECOND --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS --engine-type $ENGINE_TYPE --workers $WORKERS --cores $CORES --stats-short $STATS_SHORT --stats-timeline $STATS_TIMELINE --stats-pathway-ptime-aggregated $STATS_PATHWAY_PTIME_AGGREGATED --stats-time-aggregated $STATS_TIME_AGGREGATED --skip-prefix-length $DATASET_WARMUP_PREFIX_LENGTH --dict-size $DICT_SIZE
