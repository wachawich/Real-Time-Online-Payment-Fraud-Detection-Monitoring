FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# ใช้ -u เพื่อให้ print log ออกมาทันที ไม่ buffer
CMD ["python", "-u", "main.py"]