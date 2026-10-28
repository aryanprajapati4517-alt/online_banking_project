-- Online Banking System - database schema (MySQL 8.0+)
-- Import this file once before starting the Flask application.
CREATE DATABASE IF NOT EXISTS online_banking
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE online_banking;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NULL,
    address VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
    user_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id INT UNSIGNED NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS accounts (
    account_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id INT UNSIGNED NOT NULL,
    account_number CHAR(12) NOT NULL UNIQUE,
    account_type ENUM('SAVINGS', 'CURRENT') NOT NULL DEFAULT 'SAVINGS',
    balance DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    status ENUM('ACTIVE', 'FROZEN', 'CLOSED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_accounts_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_accounts_balance CHECK (balance >= 0.00),
    INDEX idx_accounts_customer (customer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS beneficiaries (
    beneficiary_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    customer_id INT UNSIGNED NOT NULL,
    beneficiary_account_id INT UNSIGNED NOT NULL,
    nickname VARCHAR(50) NOT NULL DEFAULT 'Recipient',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_beneficiaries_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_beneficiaries_account FOREIGN KEY (beneficiary_account_id)
        REFERENCES accounts(account_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_customer_beneficiary UNIQUE (customer_id, beneficiary_account_id),
    INDEX idx_beneficiaries_customer (customer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    from_account_id INT UNSIGNED NULL,
    to_account_id INT UNSIGNED NULL,
    transaction_type ENUM('DEPOSIT', 'WITHDRAWAL', 'TRANSFER') NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    reference_code VARCHAR(24) NOT NULL UNIQUE,
    description VARCHAR(255) NULL,
    status ENUM('SUCCESS', 'FAILED') NOT NULL DEFAULT 'SUCCESS',
    transaction_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_from_account FOREIGN KEY (from_account_id)
        REFERENCES accounts(account_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_transactions_to_account FOREIGN KEY (to_account_id)
        REFERENCES accounts(account_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_transaction_amount CHECK (amount > 0.00),
    -- Transaction direction is validated by the Flask operations before insert.
    INDEX idx_transactions_from_time (from_account_id, transaction_time),
    INDEX idx_transactions_to_time (to_account_id, transaction_time)
) ENGINE=InnoDB;

-- Optional view: transaction information with source and destination account numbers.
CREATE OR REPLACE VIEW transaction_details AS
SELECT
    t.transaction_id,
    t.reference_code,
    t.transaction_type,
    t.amount,
    t.status,
    t.description,
    t.transaction_time,
    source.account_number AS from_account_number,
    destination.account_number AS to_account_number
FROM transactions AS t
LEFT JOIN accounts AS source ON source.account_id = t.from_account_id
LEFT JOIN accounts AS destination ON destination.account_id = t.to_account_id;
