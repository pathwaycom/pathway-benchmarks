FROM python:3.10

RUN mkdir -p /public/pathway
RUN mkdir third_party
RUN mkdir .git
RUN mkdir -p /pathway-all/results

WORKDIR /pathway-all

RUN echo "remote build" \
    && pip install --no-cache-dir --upgrade pathway==0.4.1 \
    && echo $(pathway --version); 

COPY ./services/pathway-all/main.py /pathway-all/main.py

CMD echo $(pathway --version) > /pathway-all/results/pw-version.txt \
    && pathway spawn \
    --threads $CORES python main.py \
    --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS 