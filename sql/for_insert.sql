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


INSERT INTO transactions (
    step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, 
    nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud
) VALUES 
( 1, 'TRANSFER', 181.0,     'C1305486145', 181.0,      0.0,       'C553264065',   0.0, 0.0,       0,0),
( 1, 'TRANSFER', 181.0,     'C1305486145', 181.0,      0.0,       'C553264065',   0.0, 0.0,       0,0),
( 1, 'TRANSFER', 181.0,     'C1305486145', 181.0,      0.0,       'C553264065',   0.0, 0.0,       0,0)

