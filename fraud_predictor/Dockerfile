FROM python:3.9-slim

WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy โค้ดและโมเดลเข้าไป
COPY fraud_predictor.py .
COPY xgb_model.pkl .
COPY preprocessing_pipeline.pkl .

#
CMD ["python", "-u", "fraud_predictor.py"]