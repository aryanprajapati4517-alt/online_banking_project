# Project Report: Online Banking System

## 1. Title
**VaultBank — Online Banking System using Python Flask and MySQL**

## 2. Abstract
VaultBank is a web-based educational prototype that demonstrates how a banking application can manage customer profiles, login details, accounts, beneficiaries and transaction records using a relational database. The backend is written in Python using Flask, and MySQL stores the persistent data. The prototype supports registration, sign-in, account balance display, simulated deposit and withdrawal, account-to-account transfer, beneficiary management, and transaction history. The database uses primary keys, foreign keys, unique constraints, check constraints, indexes and a view. Transfer operations are grouped in a database transaction so that related balance changes and transaction-history insertion are committed together or rolled back if an error occurs.

**Scope disclaimer:** This project uses fictional balances and is not integrated with a real bank or payment system.

## 3. Problem statement
Manual banking records are difficult to search, update and maintain consistently. The aim of this project is to demonstrate a basic web interface backed by a structured database where account details and transactions can be stored, related, retrieved and updated while preserving basic data integrity.

## 4. Objectives
- Design a relational schema for customers, users, accounts, beneficiaries and transactions.
- Implement a basic website using Python Flask and HTML/CSS.
- Connect the application to MySQL using parameterized SQL queries.
- Demonstrate CRUD concepts, joins, aggregate functions, constraints and a view.
- Simulate deposit, withdrawal and transfer operations.
- Use database transactions to keep a transfer's balance changes and history record consistent.
- Provide a simple, responsive interface that can be demonstrated during a DBMS viva.

## 5. Hardware and software requirements

**Hardware:** A regular student laptop or desktop with at least 4 GB RAM and a local network/browser.

**Software:** Windows, macOS or Linux; Python 3.11+; MySQL 8.0+; MySQL Workbench (recommended); Flask; `mysql-connector-python`; `python-dotenv`; and a modern web browser.

## 6. System modules
1. **Registration and login:** Creates a customer and user login, hashes the password, and opens a demo savings account.
2. **Dashboard:** Displays the current customer's accounts, available demo balances and recent activity.
3. **Deposit:** Increases a selected active account's demo balance and records the deposit.
4. **Withdrawal:** Checks the balance, decreases it only when sufficient funds exist, and records the withdrawal.
5. **Fund transfer:** Validates the sender and receiver, locks the two account rows, checks balance, updates the debit and credit, and records a unique transaction reference.
6. **Beneficiary management:** Saves recipient accounts for reuse and allows the customer to remove their own saved beneficiary rows.
7. **Transaction history:** Lists account movements with type, amount, reference, source, destination and timestamp.

## 7. Database design

| Table | Key columns | Purpose |
|---|---|---|
| `customers` | `customer_id` (PK), `email` (UNIQUE) | Customer profile |
| `users` | `user_id` (PK), `customer_id` (FK, UNIQUE), `username` (UNIQUE) | Login identity and password hash |
| `accounts` | `account_id` (PK), `customer_id` (FK), `account_number` (UNIQUE) | Account details and balance |
| `beneficiaries` | `beneficiary_id` (PK), `customer_id` (FK), `beneficiary_account_id` (FK) | Recipient accounts saved by customers |
| `transactions` | `transaction_id` (PK), `from_account_id` (FK), `to_account_id` (FK), `reference_code` (UNIQUE) | Deposit, withdrawal and transfer ledger records |

See `ER_DIAGRAM.svg` for a visual representation and `schema.sql` for the exact constraints and view definition.

## 8. Relationship summary
- One customer has one login identity in this project's scope.
- One customer may have many accounts.
- One customer may save many beneficiary accounts.
- One account can appear in many transactions as the source and/or destination.
- A transfer uses one transaction row and references both account IDs.

## 9. Implementation overview
The browser submits HTML forms to Flask routes. Flask validates the submitted values, checks the login session, and uses `mysql-connector-python` to run parameterized SQL statements. MySQL enforces the keys and constraints. Passwords are stored using a password-hashing function instead of plain text. The interface is built with Jinja templates and responsive CSS.

For money values, the schema uses `DECIMAL(14,2)`. The transfer route starts a database transaction, checks the accounts, locks both rows in a consistent order, checks the available balance, updates both balances, inserts a ledger record and commits. Exceptions trigger rollback so a partial transfer is not committed.

## 10. Testing checklist

| Test | Expected result |
|---|---|
| Register with valid details | Customer, user and zero-balance account are created |
| Register using an existing email/username | Duplicate is rejected |
| Enter wrong login password | Login is denied |
| Deposit a positive amount | Balance increases and a history row appears |
| Withdraw less than or equal to balance | Balance decreases and history is recorded |
| Withdraw more than balance | Rejected with no balance change |
| Transfer to an active other account with sufficient funds | Sender decreases, recipient increases, one transfer row appears |
| Transfer to unknown/inactive account | Rejected |
| Try to transfer to the same account | Rejected |
| Add the same beneficiary twice | Duplicate is rejected |
| Query transaction view | Source/destination account numbers are shown with transaction data |

## 11. Limitations
The project is a small local demonstration. It does not provide real banking connectivity, KYC, OTP, email verification, a bank-grade authorization model, professional security review, or production deployment controls. The deposit and withdrawal forms simulate cash counter operations. Public demo credentials are for local teaching only.

## 12. Future enhancements
- Add a separate administrator role and account status management.
- Add password reset, email verification and OTP for a demo login.
- Add printable account statements and date filters.
- Add a stronger audit trail and automated test suite.
- Deploy behind HTTPS with managed secrets, rate limiting, monitoring and security review.
- Integrate with an approved sandbox provider if external payment simulation is required by the course.

## 13. Conclusion
VaultBank demonstrates how a simple banking interface can use a relational database to maintain customer and account records and record account movements. The project applies core DBMS ideas—keys, relationships, constraints, joins, views and transactions—in a practical Python/MySQL application. It provides a foundation for further learning while remaining a fictional, non-production simulation.
