# VaultBank — Online Banking System (DBMS Mini Project)

A second-year B.Tech DBMS mini project using **Python, Flask, HTML/CSS, and MySQL**. It demonstrates relational database design, foreign keys, constraints, SQL joins, password hashing, session login, and ACID-style transactions for simulated banking operations.

> **Educational use only:** this project uses fictional demo money. It is not connected to a real bank, UPI, NEFT, IMPS, or any payment network. Do not enter real banking credentials or sensitive personal information. It is a learning prototype, not production banking software.

## Features

- Customer registration and login; passwords are stored as password hashes.
- A MySQL customer, user, account, beneficiary, and transaction schema.
- Dashboard showing accounts, masked account numbers, and total demo balance.
- Simulated deposit and withdrawal, with insufficient-balance checks.
- Account-to-account transfers, source ownership validation, active-account checks, row locks, and one database transaction for both balances and the history record.
- Beneficiary add/list/remove features.
- Transaction history and a `transaction_details` SQL view.
- HTML form CSRF tokens, parameterized SQL statements, input validation, and a responsive interface.

## Project files

```text
online_banking_project/
├── app.py                 # Flask application and routes
├── schema.sql             # MySQL tables, constraints, indexes and view
├── seed_demo.py           # Adds two fictional demo users and opening balances
├── queries_for_demo.sql   # SQL practice / viva queries
├── requirements.txt       # Python packages
├── .env.example           # Example database and Flask configuration
├── .gitignore
├── README.md              # Installation and usage
├── VIVA_PREP.md           # Viva questions with simple answers
├── templates/             # HTML pages rendered by Flask
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── transfer.html
│   ├── beneficiaries.html
│   ├── transactions.html
│   └── error.html
└── static/
    └── style.css          # Responsive website design
```

## Step-by-step setup on Windows

### 1. Install the required software

Install **Python 3.11 or newer** and **MySQL 8.0 or newer**. MySQL Workbench is useful for running the SQL files and viewing tables. During MySQL installation, remember the password you set for the local MySQL user (often `root`).

### 2. Create the database tables

1. Open MySQL Workbench and connect to your local MySQL server.
2. Open `schema.sql` in Workbench.
3. Execute the entire script using the lightning-bolt button.
4. Refresh the Schemas panel. You should see the `online_banking` database and these tables: `customers`, `users`, `accounts`, `beneficiaries`, and `transactions`. You will also see the `transaction_details` view.

You can also import the script from a MySQL command line:

```bash
mysql -u root -p < schema.sql
```

### 3. Create a Python virtual environment

Open Command Prompt or PowerShell in the `online_banking_project` folder and run:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If Windows does not recognize `py`, try `python` instead.

### 4. Configure the MySQL connection

Copy `.env.example` and rename the copy to `.env` in the project folder. In PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set `DB_PASSWORD` to your local MySQL password. Example:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_local_mysql_password
DB_NAME=online_banking
SECRET_KEY=replace-this-with-a-long-random-secret-key
PORT=5000
FLASK_DEBUG=1
COOKIE_SECURE=0
```

`COOKIE_SECURE=0` is for local HTTP testing. `FLASK_DEBUG=1` is also only for local development. Never publish your `.env` file or expose the Flask debug server to the internet.

### 5. Add example accounts

Run:

```powershell
python seed_demo.py
```

The script creates two fictional demo users and sample opening balances. It avoids creating duplicate demo usernames when run again.

| Username | Password | Example account number on a fresh database |
|---|---|---|
| `demo1` | `LearnDBMS123!` | `100000000001` |
| `demo2` | `LearnDBMS123!` | `100000000002` |

On a fresh database, `demo1` begins with ₹25,000.00 and `demo2` begins with ₹10,000.00. If the script finds existing accounts from a previous run, it keeps those accounts rather than resetting their balances. These credentials are deliberately public sample credentials; do not reuse them outside this classroom demo.

### 6. Start the website

```powershell
python app.py
```

Open **http://127.0.0.1:5000** in your browser. Log in with `demo1` / `LearnDBMS123!` or register a new fictional demo customer.

If the browser says the server is unavailable, check that the terminal still shows Flask running. To stop it, press `Ctrl+C` in the terminal.

## Demo walkthrough for your teacher

1. Log in as `demo1` and point out the dashboard and masked account number.
2. Open **Transactions** to explain that every successful account operation creates a row in the `transactions` table.
3. Deposit ₹500 into the demo account and show the updated balance and new transaction record.
4. Try to withdraw more money than the balance. Explain that the operation is rejected and no transaction is committed.
5. Add `100000000002` as a beneficiary, then transfer a small amount to it. Show both account balances after the transfer.
6. In MySQL Workbench, run the sample `JOIN` queries in `queries_for_demo.sql` and show the relationship between customers, accounts, and transactions.
7. Explain that the transfer locks account rows and commits the debit, credit, and history insertion together. If an operation raises an error, the application rolls the transaction back.

## Database design / relationships

- `customers` 1 — 1 `users`: one login row per customer for this project's scope.
- `customers` 1 — many `accounts`: one customer may own more than one account.
- `customers` 1 — many `beneficiaries`: a customer can save multiple recipient accounts.
- `accounts` 1 — many `transactions` as a source account and/or destination account.
- `beneficiaries.beneficiary_account_id` points to an account belonging to the recipient; the application prevents saving the customer's own account as a beneficiary.

Primary keys uniquely identify rows. Foreign keys maintain referential integrity. Unique constraints protect email addresses, usernames, account numbers, transaction references, and duplicate beneficiary links. `DECIMAL(14,2)` is used for balances and amounts to avoid binary floating-point rounding in money values. The InnoDB engine supports transactional changes and row locking.

## Transaction model

- Deposit: lock the customer's active account, increase its balance, insert a `DEPOSIT` record, commit.
- Withdrawal: lock the account, check available balance, decrease it, insert a `WITHDRAWAL` record, commit.
- Transfer: validate the source and recipient, lock the two account rows in account-ID order, check available balance, debit sender, credit recipient, insert one `TRANSFER` record, commit.

The application uses SQL placeholders (`%s`) instead of building queries from form text. All user inputs are checked on the server; browser-side validation is only a convenience. The transfer history record stores both account IDs, so each side can be traced.

## Common troubleshooting

- **`ModuleNotFoundError: No module named 'flask'`:** activate `.venv` and run `pip install -r requirements.txt`.
- **`No module named 'mysql'`:** run `pip install mysql-connector-python` inside the activated virtual environment.
- **Access denied for user:** check `DB_USER` and `DB_PASSWORD` in `.env`.
- **Unknown database `online_banking`:** run `schema.sql` in MySQL Workbench first.
- **Connection refused / can't connect:** make sure your local MySQL service is running and `DB_HOST`/`DB_PORT` are correct.
- **Invalid/expired form token:** refresh the page and submit the form again.
- **Account number not found for transfer:** check the full 12-digit account number. On a fresh seed, `demo2` is `100000000002`.

## Known limitations to explain honestly in viva

This is a local student prototype. It has no OTP, KYC, bank integration, payment gateway, admin console, email verification, deployment hardening, audit infrastructure, or formal penetration testing. Deposits and withdrawals simulate teller actions. It should not be presented as production-ready banking software. For a real deployment, security design, identity verification, secure secret management, HTTPS, rate limiting, monitoring, audit logging, threat modelling, and professional review would be mandatory.
