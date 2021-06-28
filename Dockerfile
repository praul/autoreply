FROM ubuntu:bionic
WORKDIR /app
COPY ./autoreplyer.py  /app
COPY ./script.py  /app

RUN apt update && apt install -y python3 python3-pip
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir emails


CMD ["python3", "-u", "/app/script.py"]


