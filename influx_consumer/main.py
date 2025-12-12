import os
import json
import time
from kafka import KafkaConsumer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Configuration (ดึงจาก Env Vars ใน docker-compose) ---
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'fraud.predictions')

INFLUX_URL = os.getenv('INFLUX_URL', 'http://influxdb:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', 'my-super-secret-auth-token')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'qOn')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'fraud_monitoring')

# --- Setup InfluxDB Client ---
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def connect_kafka():
    # Loop รอจนกว่า Kafka จะพร้อม (Retrying connection)
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='influxdb-writer-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            print("Connected to Kafka!")
            return consumer
        except Exception as e:
            print(f"Waiting for Kafka... ({e})")
            time.sleep(5)

def process_messages():
    consumer = connect_kafka()
    
    for message in consumer:
        data = message.value
        
        try:
            features = data.get("features", {})
            
            # แปลง Timestamp จาก String เป็น Object
            timestamp_val = data.get("timestamp") 

            point = Point("fraud_transaction") \
                .time(timestamp_val) \
                .tag("model_version", data.get("model_version", "unknown")) \
                .tag("txn_type", features.get("type", "UNKNOWN")) \
                .tag("alert_status", features.get("alert", "Normal")) \
                .tag("is_fraud", int(data.get("is_fraud", 0))) \
                .field("transaction_id", str(data.get("transaction_id"))) \
                .field("is_fraud", int(data.get("is_fraud", 0))) \
                .field("risk_score", float(data.get("risk_score", 0.0))) \
                .field("amount", float(features.get("amount", 0.0))) \
                .field("old_balance_org", float(features.get("oldbalanceorg", 0.0))) \
                .field("new_balance_org", float(features.get("newbalanceorig", 0.0))) \
                .field("rules_triggered_count", int(features.get("rules_triggered", 0))) \
                .field("rule1", int(features.get("rule1", 0))) \
                .field("rule5", int(features.get("rule5", 0)))

            # เขียนลง InfluxDB
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            
            print(f"Written TX ID: {data.get('transaction_id')} | Score: {data.get('risk_score')}")
            
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
            #print(f"Problematic data: {data}")

if __name__ == "__main__":
    process_messages()