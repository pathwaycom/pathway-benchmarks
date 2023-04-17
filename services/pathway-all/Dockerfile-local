FROM python:3.10
# FROM pathway-debug
ENV USING_BENCHMARK_HARNESS=1

ARG LOCAL_BUILD_FLAG=false
ENV LOCAL_BUILD=$LOCAL_BUILD_FLAG

ARG PUBLIC_PATHWAY_DIR=.
ENV PUBLIC_PATHWAY=$PUBLIC_PATHWAY_DIR

ARG THIRD_PARTY_DIR=.
ENV THIRD_PARTY=$THIRD_PARTY_DIR

ARG DOT_GIT_DIR=.
ENV DOT_GIT=$DOT_GIT_DIR


RUN mkdir -p /public/pathway
RUN mkdir third_party
RUN mkdir .git
RUN mkdir -p /pathway-all/results

COPY $PUBLIC_PATHWAY /public/pathway
COPY $THIRD_PARTY /third_party
COPY $DOT_GIT /.git

WORKDIR /pathway-all

RUN if "$LOCAL_BUILD" == "true" ; then \
    echo "local build" \
    && cd /public/pathway \
    && export RUSTUP_HOME=/usr/local/rustup \
    && export CARGO_HOME=/usr/local/cargo \
    && export PATH=/usr/local/cargo/bin:$PATH \
    && apt-get update \
    && apt-get install -y libsasl2-dev \
    && apt-get install -y cmake \
    && curl https://sh.rustup.rs -sSf > rust-installer.sh \
    && bash rust-installer.sh -y \
    && pip install maturin \
    && maturin build --release --strip \
    && pip install /public/pathway/target/wheels/pathway-*.whl \
    && echo $(git rev-parse --short HEAD); \
else \
    echo "remote build" \
    && pip install --no-cache-dir --upgrade pathway --extra-index-url https://packages.pathway.com/966431ef6b933cbab9baf6332a9b79e50e4e3c6e42c5a6e6d3fd3767ad31aa2fe443c18312 \
    && echo $(pathway --version); \
fi

COPY ./public/pathway-benchmarks/services/pathway-all/main.py /pathway-all/main.py

CMD  if "$LOCAL_BUILD" == "true" ; then \
        cd /public/pathway \
        && echo $(git rev-parse --short HEAD) > /pathway-all/results/pw-version.txt \
        && cd /pathway-all; \
    else \
        echo $(pathway --version) > /pathway-all/results/pw-version.txt; \
fi \
&& pathway spawn \
    --threads $CORES python main.py \
    --type $BENCHMARK_TYPE \
    --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS 