FROM python:3.10

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

RUN apt-get update
WORKDIR /kafka-output-to-stderr

RUN apt-get install -y libsasl2-dev
RUN curl https://sh.rustup.rs -sSf > rust-installer.sh
RUN bash rust-installer.sh -y

COPY ./src /kafka-output-to-stderr/src
COPY ./Cargo.lock /kafka-output-to-stderr/Cargo.lock
COPY ./Cargo.toml /kafka-output-to-stderr/Cargo.toml
RUN cargo build

COPY ./main.py /kafka-output-to-stderr/main.py

CMD python main.py --type $BENCHMARK_TYPE --batch-size $COMMIT_FREQUENCY --rate-per-second $RATE_PER_SECOND --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS --engine-type $ENGINE_TYPE
