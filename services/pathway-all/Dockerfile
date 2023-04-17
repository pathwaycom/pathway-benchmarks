FROM python:3.10
# FROM pathway-debug
ENV USING_BENCHMARK_HARNESS=1

RUN mkdir -p /public/pathway
RUN mkdir third_party
RUN mkdir .git
RUN mkdir -p /pathway-all/results

WORKDIR /pathway-all

RUN echo "remote build" \
    && pip install --no-cache-dir --upgrade pathway --extra-index-url https://packages.pathway.com/966431ef6b933cbab9baf6332a9b79e50e4e3c6e42c5a6e6d3fd3767ad31aa2fe443c18312 \
    && echo $(pathway --version); 

COPY ./services/pathway-all/main.py /pathway-all/main.py

CMD echo $(pathway --version) > /pathway-all/results/pw-version.txt; \
    && pathway spawn \
        --threads $CORES python main.py \
        --type $BENCHMARK_TYPE \
        --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS 