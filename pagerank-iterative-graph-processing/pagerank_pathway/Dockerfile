FROM python:3.10

ARG DATASET_PATH
ARG AVAILABLE_CORE_IDS
ARG N_CORES_TO_TEST
ARG N_STEPS_TO_TEST
ARG REPEATS

RUN mkdir -p /pagerank-pathway

WORKDIR /pagerank-pathway

RUN echo "remote build" \
    && pip install --no-cache-dir --upgrade pathway --extra-index-url https://packages.pathway.com/966431ef6b933cbab9baf6332a9b79e50e4e3c6e42c5a6e6d3fd3767ad31aa2fe443c18312 \
    && echo $(pathway --version); 

COPY ./datasets/ /pagerank-pathway/datasets
COPY ./pagerank_pathway/doall.py /pagerank-pathway/doall.py
COPY ./pagerank_pathway/main.py /pagerank-pathway/main.py

CMD python doall.py --dataset-path ${DATASET_PATH} --available-core-ids ${AVAILABLE_CORE_IDS} --n-cores-to-test ${N_CORES_TO_TEST} --n-steps-to-test ${N_STEPS_TO_TEST} --repeats ${REPEATS}
