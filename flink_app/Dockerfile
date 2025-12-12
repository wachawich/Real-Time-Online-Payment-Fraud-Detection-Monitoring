FROM python:3.9-slim-bullseye

RUN apt-get update && \
    apt-get install -y openjdk-11-jdk-headless && \
    rm -rf /var/lib/apt/lists/*;

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

WORKDIR /app

COPY fraud_detection.py .
COPY flink-sql-connector-kafka-3.0.0-1.17.jar .

RUN pip install --default-timeout=1000 apache-flink==1.17.1

CMD ["python", "fraud_detection.py"]