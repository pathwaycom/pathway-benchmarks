FROM python:3.10

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    USING_BENCHMARK_HARNESS=1

RUN apt-get update
WORKDIR /streamer

RUN apt-get install -y libsasl2-dev
RUN curl https://sh.rustup.rs -sSf > rust-installer.sh
RUN bash rust-installer.sh -y

COPY ./src /streamer/src
COPY ./Cargo.lock /streamer/Cargo.lock
COPY ./Cargo.toml /streamer/Cargo.toml
RUN cargo build --release

COPY ./main.py /streamer/main.py
COPY ./datasets /streamer/datasets

CMD python main.py --type $BENCHMARK_TYPE --batch-size $COMMIT_FREQUENCY --rate-per-second $RATE_PER_SECOND --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS --skip-prefix-length $DATASET_WARMUP_PREFIX_LENGTH --wait-time-ms $STREAMER_WAIT_TIME_MS --emit-interval-ms $STREAMER_EMIT_INTERVAL_MS
