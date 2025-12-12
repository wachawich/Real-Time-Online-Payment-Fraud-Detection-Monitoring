CREATE TABLE transactions (
    step INTEGER,
    type VARCHAR(20),
    amount NUMERIC(15, 2),
    nameOrig VARCHAR(50),
    oldbalanceOrg NUMERIC(15, 2), -- สังเกตการสะกดตามที่คุณให้มา (Org)
    newbalanceOrig NUMERIC(15, 2),
    nameDest VARCHAR(50),
    oldbalanceDest NUMERIC(15, 2),
    newbalanceDest NUMERIC(15, 2),
    isFraud INTEGER,
    isFlaggedFraud INTEGER,
    -- เพิ่ม Primary Key เพื่อให้ Debezium ทำงานได้สมบูรณ์ (Optional แต่แนะนำ)
    id SERIAL PRIMARY KEY 
);