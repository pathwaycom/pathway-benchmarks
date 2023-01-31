FROM python:3.10
# FROM pathway-debug
WORKDIR /pathway-all

COPY ./requirements.txt /pathway-all/requirements.txt
# ENV PATHWAY_PROFILE=dev
# ENV RUST_BACKTRACE=1
RUN pip install --no-cache-dir --upgrade -r /pathway-all/requirements.txt
# RUN pip install --no-cache-dir --upgrade py-spy
COPY ./main.py /pathway-all/main.py
# CMD python main.py --type $BENCHMARK_TYPE --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS
# CMD py-spy --version
CMD python main.py --type $BENCHMARK_TYPE --autocommit-frequency-ms $AUTOCOMMIT_FREQUENCY_MS