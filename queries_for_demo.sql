-- Run after schema.sql and seed_demo.py, in MySQL Workbench.
USE online_banking;

-- 1. Inspect the relational schema.
SHOW TABLES;
DESCRIBE customers;
DESCRIBE accounts;
DESCRIBE transactions;

-- 2. Display all customers.
SELECT customer_id, full_name, email, phone, created_at
FROM customers
ORDER BY customer_id;

-- 3. JOIN: display each account with its owner's name.
SELECT c.full_name, c.email, a.account_number, a.account_type,
       a.balance, a.status
FROM customers AS c
JOIN accounts AS a ON a.customer_id = c.customer_id
ORDER BY c.full_name;

-- 4. JOIN: show transaction records with from/to account numbers.
SELECT transaction_id, reference_code, transaction_type, amount,
       from_account_number, to_account_number, status, transaction_time
FROM transaction_details
ORDER BY transaction_time DESC;

-- 5. Aggregate: total balance and number of accounts per customer.
SELECT c.customer_id, c.full_name,
       COUNT(a.account_id) AS account_count,
       COALESCE(SUM(a.balance), 0.00) AS total_balance
FROM customers AS c
LEFT JOIN accounts AS a ON a.customer_id = c.customer_id
GROUP BY c.customer_id, c.full_name
ORDER BY c.customer_id;

-- 6. Aggregate: count transactions by type.
SELECT transaction_type, COUNT(*) AS transaction_count,
       COALESCE(SUM(amount), 0.00) AS total_amount
FROM transactions
GROUP BY transaction_type;

-- 7. WHERE: find transactions above ₹1,000.
SELECT transaction_id, transaction_type, amount, reference_code, transaction_time
FROM transactions
WHERE amount > 1000.00
ORDER BY amount DESC;

-- 8. View: the view joins source and destination accounts for easier reporting.
SELECT * FROM transaction_details LIMIT 20;

-- 9. Constraint test (expected to fail because the amount must be positive):
-- INSERT INTO transactions (transaction_type, amount, reference_code)
-- VALUES ('DEPOSIT', -50.00, 'INVALID-DEMO-REF');

-- 10. Transaction syntax example only. Do not execute blindly on your project data.
-- START TRANSACTION;
-- SELECT account_id, balance FROM accounts WHERE account_id = 1 FOR UPDATE;
-- UPDATE accounts SET balance = balance + 100.00 WHERE account_id = 1;
-- INSERT INTO transactions
--   (from_account_id, to_account_id, transaction_type, amount, reference_code, description)
-- VALUES (NULL, 1, 'DEPOSIT', 100.00, 'MANUAL-DEMO-REF', 'Manual SQL demonstration');
-- COMMIT;
-- Use ROLLBACK instead of COMMIT to undo uncommitted changes.
