# 🛡️Real-Time Online Payment Fraud Detection Monitoring

![Project Status](https://img.shields.io/badge/Status-Active-success?logo=hyper&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Go](https://img.shields.io/badge/Go-00ADD8?logo=go&logoColor=white)
![Apache](https://img.shields.io/badge/Apache%20Flink-E6526F?logo=apache&logoColor=white)
![InfluxDB](https://img.shields.io/badge/InfluxDB-22ADF6?logo=influxdb&logoColor=white)


![Demo](/asset/Fraud-Project-Example.gif)

This project demonstrates a scalable, end-to-end Data Engineering and Machine Learning pipeline designed to detect payment fraud in real-time.

Instead of relying on static datasets, this system initiates by generating Synthetic Online Payment Transactions to simulate a live production environment. The core architectural decision involves a Hybrid Detection Strategy:

  1. Rule-Based Filtering (Flink): Acts as the first line of defense to filter high-volume streams using predefined business rules.
  2. ML Inference (XGBoost): Only "suspicious" transactions identified by Flink are forwarded to the Machine Learning model.

Why this approach? By using Apache Flink to pre-process and filter data, we significantly reduce the computational load and latency on the XGBoost predictor, ensuring the ML model only spends resources analyzing high-probability fraud candidates rather than every single transaction.


## 🚀 System Workflow

![Project Flow](/asset/project-flow.png)


### 1. **Synthetic Transaction Generator** :
- The Application Layer (Go Fiber) acts as a simulator, generating continuous synthetic online payment transactions and persisting them into PostgreSQL.

### 2. **Change Data Capture (CDC)** :
- Debezium listens to PostgreSQL logs (WAL) and instantly streams every transaction event into Kafka (Topic: `pg.public.transactions`).

### 3. **Level 1: Rule-Based Detection (Stream Processing)** :
- Apache Flink consumes the raw transaction stream.
- It applies real-time validation rules (e.g., detecting account draining patterns, balance calculation mismatches, high-value transfers to merchants, or transfers from empty accounts).
- Optimization: Normal transactions are ignored or routed elsewhere. Only transactions that trigger a "Risk Alert" are produced to the `fraud.features.ml` topic.

#### 🛡 Fraud Detection Rules (Flink SQL)
The following rules are applied in real-time by Apache Flink to filter suspicious transactions before sending them to the ML model:

| Rule ID | Logic Check | Description |
| --- | --- | --- |
| **Rule 1** | `Amount > 90% of Origin Balance` | Detects potential account draining behavior. |
| **Rule 2** | `Origin Balance Mismatch` | Flags if the sender's new balance is mathematically incorrect (calculation error or manipulation). |
| **Rule 3** | `Dest. Balance Mismatch` | Flags if the receiver's new balance is mathematically incorrect. |
| **Rule 4** | `Dest. Name starts with 'M'` | Identifies transfers made to Merchants (often higher risk than P2P). |
| **Rule 5** | `Amount > 200,000` | Flags unusually high-value transactions. |
| **Rule 6** | `Origin Balance = 0` | Detects transfers attempted from an empty account (system anomaly). |


### 4. **Level 2: Advanced ML Prediction** :
- The XGBoost Fraud Predictor consumes the filtered stream from Flink.
- It performs deep inference on these specific transactions to calculate a precise fraud probability score.
- Final results are sent to the `fraud.predictions` topic.

### 5. **Real-Time Monitoring** :
- An Influx Consumer service saves the prediction results into InfluxDB (Time Series Database).
- Grafana visualizes the data, providing a live dashboard for security analysts to monitor fraud trends and system performance.


## 📁 Directory Structure

```
Real-Time-Fraud-Detection-Monitoring/
├── asset/                              # Project assets and documentation images
├── clients/                            # Next.js Frontend Application
│   ├── src/
│   │   ├── components/
│   │   │   └── TransactionStreamer.tsx # Real-time transaction streaming component
│   │   ├── pages/
│   │   │   ├── _app.tsx               # Next.js app component
│   │   │   ├── _document.tsx          # Next.js document component
│   │   │   └── index.tsx              # Main page
│   │   └── styles/
│   │       └── globals.css            # Global styles
│   ├── public/
│   │   └── data/                      # Static data files
│   ├── Dockerfile                     # Docker configuration for frontend
│   ├── package.json                   # Node.js dependencies
│   └── next.config.ts                 # Next.js configuration
├── flink_app/                          # Apache Flink Stream Processing
│   ├── fraud_detection.py             # Flink job for rule-based fraud detection
│   └── Dockerfile                     # Docker configuration for Flink app
├── fraud_predictor/                    # XGBoost ML Model Service
│   ├── fraud_predictor.py             # ML inference service
│   ├── requirements.txt               # Python dependencies
│   └── Dockerfile                     # Docker configuration for ML service
├── influx_consumer/                    # InfluxDB Data Consumer
│   ├── main.py                        # Kafka to InfluxDB consumer
│   ├── requirements.txt               # Python dependencies
│   └── Dockerfile                     # Docker configuration for consumer
├── jupyter/                            # Machine Learning Development
│   └── fraud_detection_with_xgboost.ipynb # ML model training notebook
├── server/                             # Go Backend API
│   ├── database/
│   │   └── connection.go              # Database connection handler
│   ├── nginx/
│   │   └── nginx.conf                 # Nginx proxy configuration
│   ├── main.go                        # Main Go application
│   ├── go.mod                         # Go module dependencies
│   ├── server.md                      # Server documentation
│   └── Dockerfile                     # Docker configuration for backend
├── sql/                               # Database Scripts
│   ├── create_table.sql               # Table creation scripts
│   └── for_insert.sql                 # Sample data insertion scripts
├── docker-compose.yml                 # Docker Compose configuration
├── register-sqlserver.json            # Debezium connector configuration
├── CDC.md                             # Change Data Capture documentation
└── readme.md                          # Project documentation
```

## 🛠 Tech Stack

**Application Layer**
* **Language:** Go (Golang)
* **Framework:** Fiber
* **Proxy:** Nginx
* **Database:** PostgreSQL
* **API Testing:** Postman

**Streaming & Data Engineering**
* **CDC:** Debezium
* **Message Broker:** Apache Kafka
* **Stream Processing:** Apache Flink (SQL API)
* **Management:** Kafka UI

**Machine Learning**
* **Model:** XGBoost
* **Task:** Binary Classification

**Monitoring**
* **Database:** InfluxDB
* **Dashboard:** Grafana

---

## 📊 Dataset Reference

This project utilizes the **Online Payment Fraud Detection Dataset** from Kaggle for training the XGBoost machine learning model.

**Dataset Source:** [Online Payment Fraud Detection - Kaggle](https://www.kaggle.com/datasets/jainilcoder/online-payment-fraud-detection/data)

### Dataset Description

To identify online payment fraud with machine learning, we need to train a machine learning model for classifying fraudulent and non-fraudulent payments. This dataset contains historical information about fraudulent transactions which can be used to detect fraud in online payments.

### Column Descriptions

| Column | Description |
|--------|-------------|
| `step` | Represents a unit of time where 1 step equals 1 hour |
| `type` | Type of online transaction (PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN) |
| `amount` | The amount of the transaction |
| `nameOrig` | Customer starting the transaction |
| `oldbalanceOrg` | Balance before the transaction |
| `newbalanceOrig` | Balance after the transaction |
| `nameDest` | Recipient of the transaction |
| `oldbalanceDest` | Initial balance of recipient before the transaction |
| `newbalanceDest` | The new balance of recipient after the transaction |
| `isFraud` | Binary indicator of fraud transaction (0 = Normal, 1 = Fraud) |
| `isFlaggedFraud` | Business model flag for illegal attempts |

This dataset enables the system to learn patterns and characteristics of fraudulent transactions, allowing the XGBoost model to make accurate predictions on new, unseen transaction data in real-time.

---

## 🤖 Machine Learning Model Development

### XGBoost Model Training

The fraud detection system uses **XGBoost (Extreme Gradient Boosting)** as the core machine learning algorithm. The complete model development process is documented in the Jupyter notebook: [`fraud_detection_with_xgboost.ipynb`](jupyter/fraud_detection_with_xgboost.ipynb).

#### 📊 Feature Engineering

The model incorporates several engineered features to improve fraud detection accuracy:

| Feature | Description | Formula |
|---------|-------------|---------|
| `diffOrig` | Origin account balance discrepancy | `oldbalanceOrg - newbalanceOrig - amount` |
| `diffDest` | Destination account balance discrepancy | `newbalanceDest - oldbalanceDest - amount` |
| `hour` | Transaction hour (0-23) | `step % 24` |
| `relativeAmount` | Amount relative to origin balance | `amount / (oldbalanceOrg + 1)` |

#### 🎯 Model Configuration

```python
xgb_model = XGBClassifier(
    n_estimators=500,
    learning_rate=0.1,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=773.75,  # Handle class imbalance
    random_state=42,
    n_jobs=-1
)
```

#### 🔧 Data Preprocessing Pipeline

1. **Data Cleaning**: Remove irrelevant columns (`nameOrig`, `nameDest`, `isFlaggedFraud`)
2. **Feature Engineering**: Create derived features for better fraud pattern detection
3. **Encoding**: One-hot encoding for categorical variables
4. **Scaling**: StandardScaler for numerical features
5. **Class Balancing**: Use `scale_pos_weight` to handle imbalanced dataset

#### 📈 Model Performance

The XGBoost model achieves high performance in fraud detection:
- **ROC-AUC Score**: > 0.95
- **Precision**: High precision to minimize false positives
- **Recall**: Optimized to catch most fraudulent transactions
- **Feature Importance**: `diffOrig` and `diffDest` are top indicators of fraud

#### 💾 Model Export & Deployment

The trained model and preprocessing pipeline are exported as pickle files:
```python
# Export trained model
with open("xgb_model.pkl", "wb") as f:
    pickle.dump(xgb_model, f)

# Export preprocessing pipeline
with open("preprocessing_pipeline.pkl", "wb") as f:
    pickle.dump(pipeline, f)
```

These serialized models are then integrated into the [`fraud_predictor.py`](fraud_predictor/fraud_predictor.py) service for real-time inference.

#### 🚀 Integration with Stream Processing

The ML model works in conjunction with Apache Flink:
1. **Flink** filters transactions using business rules
2. **XGBoost** performs deep learning inference on suspicious transactions only
3. **Results** are streamed to Kafka topic `fraud.predictions`

This hybrid approach ensures **low latency** and **high accuracy** while optimizing computational resources.

---

## 📦 Prerequisites
Ensure you have the following installed locally:
* [Docker](https://www.docker.com/)
* [Docker Compose](https://docs.docker.com/compose/)

---

## 🌐 Service Endpoints

### 🖥️ User Interfaces (Dashboards & Clients)
* **Next.js Frontend:** `http://localhost:3001`
  * *Web Application for users.*
* **Grafana Dashboard:** `http://localhost:3000`
  * *Real-time monitoring dashboard.*
  * **Login:** `admin` / `password12345`
* **Kafka UI:** `http://localhost:8080`
  * *Manage topics and view stream messages.*
* **InfluxDB UI:** `http://localhost:8086`
  * *Time-series database management.*
  * **Login:** `admin` / `password12345`

### ⚙️ APIs & Infrastructure
* **Application API (Nginx):** `http://localhost:80`
  * *Main entry point for the Backend API.*
* **Debezium Connect API:** `http://localhost:8083`
  * *REST API for managing CDC connectors.*
* **PostgreSQL:** `localhost:5432`
  * **Creds:** `postgres` / `postgres`
* **Kafka Broker:** `localhost:9092`
  * *External access for producers/consumers.*

## How to Use

### It consists of 3 parts:
* **CDC & Transactions Predictor**
* **Grafana Visualize & InfluxDB Time Series Store**
* **Run Synthetic Transactions on Web & Server**

#### 🖥️ CDC & Transactions Predictor

1. **Clone the repository:**
    ```bash
    git clone [https://github.com/wachawich/Real-Time-Online-Payment-Fraud-Detection-Monitoring.git](https://github.com/wachawich/Real-Time-Online-Payment-Fraud-Detection-Monitoring.git)
    cd Real-Time-Online-Payment-Fraud-Detection-Monitoring
    ```

2. **Start the services:**
    This command will spin up all containers (Postgres, Kafka, Flink, ML Model, Grafana, etc.).
    ```bash
    docker-compose up -d --build --scale app=3 # app is a count of load balance service
    ```

3. **Connect Local Database with pgAdmin**

```
host : localhost
user : postgres
password : postgres
port : 5432
db name : maindb
```

4. **Create Database Table**
```sql
CREATE TABLE transactions (
    step INTEGER,
    type VARCHAR(20),
    amount NUMERIC(15, 2),
    nameOrig VARCHAR(50),
    oldbalanceOrg NUMERIC(15, 2),
    newbalanceOrig NUMERIC(15, 2),
    nameDest VARCHAR(50),
    oldbalanceDest NUMERIC(15, 2),
    newbalanceDest NUMERIC(15, 2),
    isFraud INTEGER,
    isFlaggedFraud INTEGER,
    id SERIAL PRIMARY KEY 
);
```

5. **CDC Connector Setup**

* 5.1 Open Postman and Send API with
```
Method : Put
Content-Type : application/json
Host : http://localhost:8083/connectors/postgres-connector/config
```
* 5.2 Json Body
```json
{
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "postgres",
    "database.dbname" : "maindb",
    "topic.prefix": "pg",
    "plugin.name": "pgoutput",
    "table.include.list": "public.transactions",
    "decimal.handling.mode": "string",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter.schemas.enable": "false"
}
```
* 5.3 Test Insert Transactions
```sql
INSERT INTO transactions (
    step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, 
    nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud
) VALUES (
    1, 
    'TRANSFER', 
    290000.00,  
    'C12345001', 
    300000.00,  
    10000.00, 
    'C55555001', 
    0.00, 
    290000.00, 
    0, 0
);
```

* 5.4 Wait a minute and go to `http://localhost:8080/`

* 5.5 You will find topic `pg.public.transactions`, `fraud.features.ml`, `fraud.predictions` it is done!


6. If you want to test insert some transactions to DB
```sql
INSERT INTO transactions (
    step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, 
    nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud
) VALUES 
( 1, 'TRANSFER', 181.0,     'C1305486145', 181.0,      0.0,       'C553264065',   0.0, 0.0,       0,0),
( 1, 'TRANSFER', 181.0,     'C1305486145', 181.0,      0.0,       'C553264065',   0.0, 0.0,       0,0),
( 1, 'TRANSFER', 181.0,     'C1305486145', 181.0,      0.0,       'C553264065',   0.0, 0.0,       0,0);
```

7. Look at the topic `fraud.predictions`, you will see the transactions that have been predicted.

---

#### 📊 Grafana Visualize & InfluxDB Time Series Store

1. **Docker Compose Connection:**
   The Docker Compose setup has already connected the InfluxDB container with the Influx consumer service.

2. **Verify InfluxDB (Optional):**
   If you want to inspect InfluxDB directly, go to `http://localhost:8086` and login:
   * **Username:** `admin`
   * **Password:** `password12345`

   Click on the **Load Data** icon (`⬆️`) on the left navigation bar -> Select **Buckets**. You should find the `fraud_monitoring` bucket listed there.

3. **Login to Grafana:**
   Go to `http://localhost:3000` and login:
   * **Username:** `admin`
   * **Password:** `password12345`

4. **Add Data Source:**
   * Look at the left sidebar menu.
   * Click on **Connections** -> **Data sources**.
   * Click the **"Add new data source"** button (usually located in the center or top-right corner).

5. **Configure InfluxDB Data Source:**
   In the **Time series databases** category, select **InfluxDB** and configure the following settings:

   * **Name:** `influxdb`
   * **Query Language:** `Flux`

   **HTTP**
   * **URL:** `http://influxdb:8086`
   * **Allowed cookies:** *(empty)*
   * **Timeout:** *(empty)*

   **Auth**
   * Turn **OFF** all options in the Auth section (Basic Auth, TLS Client Auth, etc.).

   **InfluxDB Details**
   * **Organization:** `qOn`
   * **Token:** `my-super-secret-auth-token`
   * **Default Bucket:** `fraud_monitoring`
   * **Min time interval:** `1`
   * **Max series:** `1000`

   Click **Save & Test**.

6. **Create a Dashboard:**
   * Go to **Dashboards** (left menu).
   * Create a new dashboard and add a visualization.
   * Select the `influxdb` data source.
   * Paste the following **Flux Query** into the query editor box:

   ```flux
   from(bucket: "fraud_monitoring")
     |> range(start: -1h)
     |> filter(fn: (r) => r["_measurement"] == "fraud_transaction")
     |> filter(fn: (r) => r["_field"] == "is_fraud")
     |> filter(fn: (r) => r["_value"] == 0) # This is Normal Transactions query, You can change to 1 for Fraud Transactions
     |> aggregateWindow(every: 5s, fn: count)
     |> sort(columns: ["_time"], desc: true)
     |> yield(name: "Normal")
   ```

You can now configure the panel settings (Title, Color, Legend) on the right sidebar. Feel free to add more panels or change visualization types (e.g., Stat, Gauge, Bar Chart) to suit your monitoring needs!

---

#### Run Synthetic Transactions on Web & Server
1. **Monitor Real-Time Logs:**
   Open your terminal and run the following command to see traffic hitting the server:
   `docker-compose logs -f nginx`
2. **Open the Web Interface:**
   Open `http://localhost:3001` For open Webpage

3. Start Simulation (On Webpage):
* Click `Load Transactions` to prepare the synthetic data.
* Adjust the `Transactions per Second` to control the flow rate.
* Click `Start Streaming` to begin sending real-time transactions.

4. Observe:
* Watch the `Nginx terminal` to see the requests flowing in.
* Go to `Grafana` to watch the metrics update in real-time!

---

## 📄 License & Author

### 👨‍💻 Author
**wachawich** - *Project Developer & Maintainer*
- GitHub: [@wachawich](https://github.com/wachawich)
- Repository: [Real-Time-Fraud-Detection-Monitoring](https://github.com/wachawich/Real-Time-Fraud-Detection-Monitoring)

### 📋 License
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments
- **Kaggle Dataset:** [Online Payment Fraud Detection Dataset](https://www.kaggle.com/datasets/jainilcoder/online-payment-fraud-detection/data) by jainilcoder
- **Apache Flink Community** for the powerful stream processing framework
- **XGBoost Team** for the excellent machine learning library
- **Docker Community** for containerization support
- **Open Source Contributors** who made the various technologies in this project possible


---

⭐ **If you find this project helpful, please consider giving it a star on GitHub!** ⭐



