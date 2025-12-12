import os
from pyflink.table import EnvironmentSettings, TableEnvironment

def main():
    # 1. Setup Environment
    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    # 2. Load JAR
    # ตรวจสอบ path ให้ดีว่าใน container ไฟล์อยู่ที่นี่จริง
    jar_path = "file:///app/flink-sql-connector-kafka-3.0.0-1.17.jar"
    t_env.get_config().get_configuration().set_string("pipeline.jars", jar_path)

    print("🚀 Debugging Pipeline Started...")

    # 3. Create Source Table
    # CHANGE 1: เปลี่ยนเป็น 'earliest-offset' เพื่อให้อ่านข้อมูลเก่าที่มีอยู่แล้วออกมาด้วย
    t_env.execute_sql("""
        CREATE TABLE transactions_source (
            id INT,
            step INT,
            type STRING,
            amount STRING,
            nameorig STRING,
            oldbalanceorg STRING,
            newbalanceorig STRING,
            namedest STRING,
            oldbalancedest STRING,
            newbalancedest STRING,
            isfraud INT,
            isflaggedfraud INT
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'pg.public.transactions',
            'properties.bootstrap.servers' = 'kafka:29092',
            'properties.group.id' = 'fraud-debug-group-001', 
            'scan.startup.mode' = 'earliest-offset',  -- <--- แก้ตรงนี้สำคัญมาก!
            'format' = 'debezium-json',
            'debezium-json.schema-include' = 'false'
        )
    """)

    # 4. Create Debug Sink (Print Connector)
    # อันนี้จะช่วยให้เห็นข้อมูลที่ TaskManager logs
    t_env.execute_sql("""
        CREATE TABLE debug_print_sink (
            id INT,
            amount DECIMAL(15, 2),
            rule1 INT,
            rule2 INT,
            rule3 INT,
            rules_triggered INT,
            alert STRING
        ) WITH (
            'connector' = 'print'
        )
    """)

    # 5. Create Real Sink (Upsert Kafka)
    t_env.execute_sql("""
        CREATE TABLE fraud_features_sink (
            id INT,
            step INT,
            type STRING,
            amount DECIMAL(15, 2),
            nameorig STRING,
            oldbalanceorg DECIMAL(15, 2),
            newbalanceorig DECIMAL(15, 2),
            namedest STRING,
            oldbalancedest DECIMAL(15, 2),
            newbalancedest DECIMAL(15, 2),
            rule1 INT,
            rule2 INT,
            rule3 INT,
            rule4 INT,
            rule5 INT,
            rule6 INT,
            rules_triggered INT,
            alert STRING,
            PRIMARY KEY (id) NOT ENFORCED
        ) WITH (
            'connector' = 'upsert-kafka',
            'topic' = 'fraud.features.ml',
            'properties.bootstrap.servers' = 'kafka:29092',
            'key.format' = 'json',
            'value.format' = 'json'
        )
    """)

    # 6. View Calculation (Logic เดิม)
    t_env.execute_sql("""
        CREATE TEMPORARY VIEW rule_calculation_view AS
        SELECT
            id, step, type,
            CAST(amount AS DECIMAL(15, 2)) AS amount,
            nameorig,
            CAST(oldbalanceorg AS DECIMAL(15, 2)) AS oldbalanceorg,
            CAST(newbalanceorig AS DECIMAL(15, 2)) AS newbalanceorig,
            namedest,
            CAST(oldbalancedest AS DECIMAL(15, 2)) AS oldbalancedest,
            CAST(newbalancedest AS DECIMAL(15, 2)) AS newbalancedest,
            
            -- Rule 1
            CASE WHEN CAST(oldbalanceorg AS DECIMAL(15,2)) > 0 AND CAST(amount AS DECIMAL(15,2)) / CAST(oldbalanceorg AS DECIMAL(15,2)) > 0.9 THEN 1 ELSE 0 END AS rule1,
            -- Rule 2
            CASE WHEN ABS((CAST(oldbalanceorg AS DECIMAL(15,2)) - CAST(amount AS DECIMAL(15,2))) - CAST(newbalanceorig AS DECIMAL(15,2))) > 1 THEN 1 ELSE 0 END AS rule2,
            -- Rule 3
            CASE WHEN ABS((CAST(oldbalancedest AS DECIMAL(15,2)) + CAST(amount AS DECIMAL(15,2))) - CAST(newbalancedest AS DECIMAL(15,2))) > 1 THEN 1 ELSE 0 END AS rule3,
            -- Rule 4
            CASE WHEN namedest LIKE 'M%' THEN 1 ELSE 0 END AS rule4,
            -- Rule 5
            CASE WHEN CAST(amount AS DECIMAL(15,2)) > 200000 THEN 1 ELSE 0 END AS rule5,
            -- Rule 6
            CASE WHEN CAST(oldbalanceorg AS DECIMAL(15,2)) = 0 AND CAST(amount AS DECIMAL(15,2)) > 0 THEN 1 ELSE 0 END AS rule6
        FROM transactions_source
    """)

    # ============================================================
    # DEBUG STEP: ใช้ StatementSet เพื่อรันทั้ง Print และ Kafka Sink พร้อมกัน
    # หรือเลือกรันแค่อันใดอันหนึ่งเพื่อทดสอบ
    # ============================================================
    
    statement_set = t_env.create_statement_set()

    # Job 1: Print ลง Console (เพื่อดูว่าข้อมูลผ่าน Logic ไหม และหน้าตาเป็นยังไง)
    # ผมเอา WHERE ออกเพื่อให้เห็นทุก Transaction ว่ามันเข้ามาไหม
    statement_set.add_insert_sql("""
        INSERT INTO debug_print_sink
        SELECT 
            id, 
            amount, 
            rule1, 
            rule2, 
            rule3,
            (rule1 + rule2 + rule3 + rule4 + rule5 + rule6) as rules_triggered,
            'DEBUG_LOG'
        FROM rule_calculation_view
    """)

    # Job 2: ยิงลง Kafka (อันจริง)
    # ใส่ WHERE กลับเข้าไปได้ถ้าต้องการกรอง
    statement_set.add_insert_sql("""
        INSERT INTO fraud_features_sink
        SELECT 
            id, step, type, amount, nameorig, oldbalanceorg, newbalanceorig,
            namedest, oldbalancedest, newbalancedest,
            rule1, rule2, rule3, rule4, rule5, rule6,
            (rule1 + rule2 + rule3 + rule4 + rule5 + rule6) as rules_triggered,
            '🚨 Suspicious Transaction' AS alert
        FROM rule_calculation_view
        WHERE (rule1 + rule2 + rule3 + rule4 + rule5 + rule6) >= 2 
    """)

    job_result = statement_set.execute()
    
    print("Job Submitted! ⏳ Waiting for data... (กด Ctrl+C เพื่อหยุด)")
    # print("Job Submitted with Debug Sink!")
    job_result.wait()

if __name__ == '__main__':
    main()
