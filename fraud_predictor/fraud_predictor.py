import json
import joblib
import pandas as pd
import numpy as np
from kafka import KafkaConsumer, KafkaProducer  # <--- 1. เพิ่ม KafkaProducer
import os
import sys
import pickle
import datetime # <--- เพิ่มเพื่อใส่ timestamp

# ==========================================
# 1. SETUP CONFIG
# ==========================================
KAFKA_INPUT_TOPIC = 'fraud.features.ml'     # Topic ขาเข้า (Features)
KAFKA_OUTPUT_TOPIC = 'fraud.predictions'    # <--- 2. Topic ขาออก (ผลลัพธ์)
KAFKA_BOOTSTRAP_SERVERS = 'kafka:29092'
MODEL_PATH = 'xgb_model.pkl'
PIPELINE_PATH = 'preprocessing_pipeline.pkl'

# ==========================================
# 2. LOAD RESOURCES
# ==========================================
def load_resources():
    # ... (ส่วนนี้เหมือนเดิม) ...
    model = None
    pipeline = None
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
            print("✅ XGBoost Model loaded successfully.")
    else:
        print(f"❌ Error: Model file not found at {MODEL_PATH}")
        sys.exit(1)

    if os.path.exists(PIPELINE_PATH):
        with open(PIPELINE_PATH, "rb") as f:
            pipeline = pickle.load(f)
            print("✅ Preprocessing Pipeline loaded successfully.")
    else:
        print(f"❌ Error: Pipeline file not found at {PIPELINE_PATH}")
        sys.exit(1)
    return model, pipeline

# ==========================================
# 3. FEATURE ENGINEERING
# ==========================================
def feature_engineering(df):
    # ... (ส่วนนี้เหมือนเดิม) ...
    df["diffOrig"] = df["oldbalanceOrg"] - df["newbalanceOrig"] - df["amount"]
    df["diffDest"] = df["newbalanceDest"] - df["oldbalanceDest"] - df["amount"]
    df["hour"] = df["step"] % 24
    return df

def prepare_input_dataframe(data):
    # ... (ส่วนนี้เหมือนเดิม) ...
    try:
        features = {
            'step': [int(data.get('step', 1))], 
            'type': [str(data.get('type', 'PAYMENT'))],
            'amount': [float(data.get('amount', 0.0))],
            'oldbalanceOrg': [float(data.get('oldbalanceorg', 0.0))],
            'newbalanceOrig': [float(data.get('newbalanceorig', 0.0))],
            'oldbalanceDest': [float(data.get('oldbalancedest', 0.0))],
            'newbalanceDest': [float(data.get('newbalancedest', 0.0))],
        }
        df = pd.DataFrame(features)
        df = feature_engineering(df)
        return df
    except Exception as e:
        print(f"⚠️ Error preparing dataframe: {e}")
        return None

# ==========================================
# 4. MAIN PROCESS
# ==========================================
def main():
    print("🚀 Fraud Predictor Service Started...")
    
    loaded_model, loaded_pipeline = load_resources()

    # --- SETUP KAFKA PRODUCER (เพิ่มใหม่) ---
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8') # แปลง Dict เป็น JSON Bytes อัตโนมัติ
        )
        print(f"✅ Producer ready for output topic: {KAFKA_OUTPUT_TOPIC}")
    except Exception as e:
        print(f"❌ Kafka Producer Connection Failed: {e}")
        return
    # --------------------------------------

    try:
        consumer = KafkaConsumer(
            KAFKA_INPUT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='fraud-predictor-group-prod',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print(f"✅ Consumer connected to input topic: {KAFKA_INPUT_TOPIC}")
    except Exception as e:
        print(f"❌ Kafka Consumer Connection Failed: {e}")
        return

    print("Listening for transactions...")

    for message in consumer:
        try:
            transaction_data = message.value
            txn_id = transaction_data.get('id', 'N/A')
            
            # --- Preprocessing ---
            df_input = prepare_input_dataframe(transaction_data)
            if df_input is None: continue

            X_processed = loaded_pipeline.transform(df_input)

            # --- Prediction ---
            prediction = loaded_model.predict(X_processed)[0]
            fraud_prob = loaded_model.predict_proba(X_processed)[0][1]

            result_payload = {
                'transaction_id': txn_id,
                'is_fraud': int(prediction),         
                'risk_score': float(fraud_prob),  
                'timestamp': datetime.datetime.now().isoformat(),
                'model_version': 'XGB v1.0',
                'features': transaction_data
            }

            # --- ส่งผลลัพธ์ไป Kafka Output Topic ---
            producer.send(KAFKA_OUTPUT_TOPIC, value=result_payload)
            # producer.flush() # เปิดบรรทัดนี้ถ้าต้องการให้ส่งทันทีทีละข้อความ (จะช้าลงนิดหน่อย)

            # --- Logging ---
            if prediction == 1:
                print(f"🚨 FRAUD DETECTED! ID: {txn_id} | Score: {fraud_prob:.2%} -> Sent to Kafka")
            else:
                if fraud_prob > 0.3:
                    print(f"⚠️ Suspicious. ID: {txn_id} | Score: {fraud_prob:.2%} -> Sent to Kafka")
                else:
                    print(f"✅ Normal. ID: {txn_id} | Score: {fraud_prob:.2%} -> Sent to Kafka")

        except Exception as e:
            print(f"❌ Processing Error: {e}")

if __name__ == '__main__':
    main()