"""Create fictional demo users with balances for classroom testing.

Run after importing schema.sql. Safe to run again: it avoids duplicate demo users,
accounts and the example beneficiary. Passwords are for the local demo only.
"""
import os
import secrets
import mysql.connector
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "online_banking"),
    "charset": "utf8mb4",
    "use_unicode": True,
}

DEMO_USERS = [
    {
        "username": "demo1",
        "password": "LearnDBMS123!",
        "name": "Aarav Mehta",
        "email": "aarav.demo@example.test",
        "phone": "9000000001",
        "account_number": "100000000001",
        "opening_balance": "25000.00",
    },
    {
        "username": "demo2",
        "password": "LearnDBMS123!",
        "name": "Priya Shah",
        "email": "priya.demo@example.test",
        "phone": "9000000002",
        "account_number": "100000000002",
        "opening_balance": "10000.00",
    },
]


def random_account_number():
    return "10" + f"{secrets.randbelow(10**10):010d}"


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    demo_customer_ids = {}
    demo_account_ids = {}
    try:
        for demo in DEMO_USERS:
            cursor.execute("SELECT user_id, customer_id FROM users WHERE username = %s", (demo["username"],))
            user = cursor.fetchone()
            if user:
                customer_id = user["customer_id"]
            else:
                cursor.execute(
                    "INSERT INTO customers (full_name, email, phone, address) VALUES (%s, %s, %s, %s)",
                    (demo["name"], demo["email"], demo["phone"], "Demo address"),
                )
                customer_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO users (customer_id, username, password_hash) VALUES (%s, %s, %s)",
                    (customer_id, demo["username"], generate_password_hash(demo["password"])),
                )
                print(f"Created demo login: {demo['username']}")

            cursor.execute(
                "SELECT account_id, account_number FROM accounts WHERE customer_id = %s ORDER BY account_id LIMIT 1",
                (customer_id,),
            )
            account = cursor.fetchone()
            if account:
                account_id = account["account_id"]
            else:
                account_number = demo["account_number"]
                cursor.execute("SELECT account_id FROM accounts WHERE account_number = %s", (account_number,))
                if cursor.fetchone():
                    account_number = random_account_number()
                cursor.execute(
                    "INSERT INTO accounts (customer_id, account_number, account_type, balance) VALUES (%s, %s, 'SAVINGS', %s)",
                    (customer_id, account_number, demo["opening_balance"]),
                )
                account_id = cursor.lastrowid
                cursor.execute(
                    """INSERT INTO transactions
                       (from_account_id, to_account_id, transaction_type, amount, reference_code, description)
                       VALUES (NULL, %s, 'DEPOSIT', %s, %s, 'Seeded demo opening balance')""",
                    (account_id, demo["opening_balance"], "SEED" + secrets.token_hex(5).upper()),
                )
            demo_customer_ids[demo["username"]] = customer_id
            demo_account_ids[demo["username"]] = account_id

        cursor.execute(
            "SELECT beneficiary_id FROM beneficiaries WHERE customer_id = %s AND beneficiary_account_id = %s",
            (demo_customer_ids["demo1"], demo_account_ids["demo2"]),
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO beneficiaries (customer_id, beneficiary_account_id, nickname) VALUES (%s, %s, %s)",
                (demo_customer_ids["demo1"], demo_account_ids["demo2"], "Priya Demo"),
            )
        conn.commit()
        print("Demo data is ready.")
        print("Login 1: username=demo1, password=LearnDBMS123!")
        print("Login 2: username=demo2, password=LearnDBMS123!")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
