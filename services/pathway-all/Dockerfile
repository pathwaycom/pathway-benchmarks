FROM python:3.10
WORKDIR /pathway-all

COPY ./requirements.txt /pathway-all/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /pathway-all/requirements.txt

COPY ./main.py /pathway-all/main.py
CMD python main.py --type $BENCHMARK_TYPE --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS
