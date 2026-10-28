"""Educational Online Banking System built with Flask and MySQL.

This app simulates banking operations with fictional/demo money only.
Do not connect it to real bank accounts or use it as a production banking system.
"""

import os
import secrets
import tempfile
from pathlib import Path
from decimal import Decimal, InvalidOperation
from functools import wraps

import mysql.connector
from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
if os.getenv("FLASK_DEBUG", "1") != "1" and not secret_key:
    raise RuntimeError("SECRET_KEY must be set when FLASK_DEBUG is disabled.")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=secret_key or "local-development-key-change-this",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Set COOKIE_SECURE=1 only when running behind HTTPS.
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
)

@app.template_filter("inr")
def format_inr(value):
    return f"₹{Decimal(str(value)):,.2f}"


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "online_banking"),
    "charset": "utf8mb4",
    "use_unicode": True,
}

# DB_SSL_CA may be either a provider CA file path or PEM content from
# Render's private environment settings.
_db_ssl_ca = os.getenv("DB_SSL_CA")
if _db_ssl_ca:
    if "-----BEGIN CERTIFICATE-----" in _db_ssl_ca:
        _ca_path = Path(tempfile.gettempdir()) / "aiven-mysql-ca.pem"
        _ca_path.write_text(_db_ssl_ca.rstrip() + "\n", encoding="utf-8")
        _db_ssl_ca = str(_ca_path)
    DB_CONFIG.update(
        ssl_ca=_db_ssl_ca,
        ssl_verify_cert=True,
        ssl_verify_identity=True,
    )


def get_db():
    """Open a new MySQL connection for one request/operation."""
    return mysql.connector.connect(**DB_CONFIG)


def close_db(conn, cursor=None):
    if cursor is not None:
        try:
            cursor.close()
        except Exception:
            pass
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def new_account_number():
    """Return a fictional 12-digit account number."""
    return "10" + f"{secrets.randbelow(10**10):010d}"


def new_reference():
    return "TXN" + secrets.token_hex(6).upper()


def parse_money(raw_value):
    """Return a positive Decimal with no more than two decimal places."""
    try:
        amount = Decimal((raw_value or "").strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("Enter a valid amount, for example 250 or 250.50.")
    if not amount.is_finite() or amount <= Decimal("0"):
        raise ValueError("Amount must be greater than zero.")
    # Check the upper bound before quantize, so huge user-supplied decimals are rejected cleanly.
    if amount > Decimal("10000000.00"):
        raise ValueError("For this demo, the maximum single transaction is ₹1,00,00,000.")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("Amount can have a maximum of two decimal places.")
    return amount.quantize(Decimal("0.01"))


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


@app.before_request
def protect_post_requests():
    """Small session-based CSRF check for all HTML form POST requests."""
    if request.method == "POST":
        expected = session.get("_csrf_token", "")
        supplied = request.form.get("_csrf_token", "")
        if not expected or not supplied or not secrets.compare_digest(expected, supplied):
            abort(400, description="The form token was missing or expired. Refresh the page and try again.")


@app.context_processor
def inject_template_helpers():
    def csrf_token():
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_urlsafe(32)
        return session["_csrf_token"]
    return {"csrf_token": csrf_token}


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not username or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("register.html")
        if len(username) < 4 or len(username) > 50:
            flash("Username must be between 4 and 50 characters.", "danger")
            return render_template("register.html")
        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        conn = cursor = None
        try:
            conn = get_db()
            conn.start_transaction()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (full_name, email, phone, address) VALUES (%s, %s, %s, %s)",
                (full_name, email, phone or None, address or None),
            )
            customer_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO users (customer_id, username, password_hash) VALUES (%s, %s, %s)",
                (customer_id, username, generate_password_hash(password)),
            )
            # Unique constraint handles the extremely unlikely account-number collision.
            account_number = new_account_number()
            cursor.execute(
                "INSERT INTO accounts (customer_id, account_number, account_type, balance) VALUES (%s, %s, 'SAVINGS', 0.00)",
                (customer_id, account_number),
            )
            conn.commit()
            flash(f"Registration successful. Your demo account number is {account_number}.", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            if conn:
                conn.rollback()
            flash("That username or email is already registered. Please use a different one.", "danger")
        finally:
            close_db(conn, cursor)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        conn = cursor = None
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT u.user_id, u.username, u.password_hash, c.customer_id, c.full_name
                   FROM users u JOIN customers c ON c.customer_id = u.customer_id
                   WHERE u.username = %s""",
                (username,),
            )
            user = cursor.fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["user_id"]
                session["customer_id"] = user["customer_id"]
                session["username"] = user["username"]
                session["full_name"] = user["full_name"]
                # CSRF token is regenerated after login.
                session["_csrf_token"] = secrets.token_urlsafe(32)
                return redirect(url_for("dashboard"))
            flash("Incorrect username or password.", "danger")
        finally:
            close_db(conn, cursor)

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


def fetch_customer_accounts(cursor, customer_id):
    cursor.execute(
        """SELECT account_id, account_number, account_type, balance, status, created_at
           FROM accounts WHERE customer_id = %s ORDER BY account_id""",
        (customer_id,),
    )
    return cursor.fetchall()


def fetch_customer_transactions(cursor, customer_id, limit=10):
    cursor.execute(
        """SELECT t.transaction_id, t.transaction_type, t.amount, t.transaction_time,
                  t.reference_code, t.description, t.status,
                  fa.account_number AS from_account_number,
                  ta.account_number AS to_account_number
           FROM transactions t
           LEFT JOIN accounts fa ON fa.account_id = t.from_account_id
           LEFT JOIN accounts ta ON ta.account_id = t.to_account_id
           WHERE t.from_account_id IN
                 (SELECT account_id FROM accounts WHERE customer_id = %s)
              OR t.to_account_id IN
                 (SELECT account_id FROM accounts WHERE customer_id = %s)
           ORDER BY t.transaction_time DESC, t.transaction_id DESC
           LIMIT %s""",
        (customer_id, customer_id, limit),
    )
    return cursor.fetchall()


@app.route("/dashboard")
@login_required
def dashboard():
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        accounts = fetch_customer_accounts(cursor, session["customer_id"])
        transactions = fetch_customer_transactions(cursor, session["customer_id"], 8)
        total_balance = sum((Decimal(str(a["balance"])) for a in accounts), Decimal("0.00"))
        return render_template(
            "dashboard.html", accounts=accounts, transactions=transactions,
            total_balance=total_balance,
        )
    finally:
        close_db(conn, cursor)


def owned_active_account(cursor, account_id, customer_id, lock=False):
    sql = "SELECT account_id, account_number, balance, status FROM accounts WHERE account_id = %s AND customer_id = %s AND status = 'ACTIVE'"
    if lock:
        sql += " FOR UPDATE"
    cursor.execute(sql, (account_id, customer_id))
    return cursor.fetchone()


@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    try:
        account_id = int(request.form.get("account_id", ""))
        amount = parse_money(request.form.get("amount"))
    except (ValueError, TypeError):
        flash("Please select an account and enter a valid deposit amount.", "danger")
        return redirect(url_for("dashboard"))

    conn = cursor = None
    try:
        conn = get_db()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        account = owned_active_account(cursor, account_id, session["customer_id"], lock=True)
        if not account:
            conn.rollback()
            flash("Account not found or inactive.", "danger")
            return redirect(url_for("dashboard"))
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s", (amount, account_id))
        cursor.execute(
            """INSERT INTO transactions
               (from_account_id, to_account_id, transaction_type, amount, reference_code, description)
               VALUES (NULL, %s, 'DEPOSIT', %s, %s, 'Demo cash deposit')""",
            (account_id, amount, new_reference()),
        )
        conn.commit()
        flash(f"Demo deposit of ₹{amount:,.2f} completed.", "success")
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        close_db(conn, cursor)
    return redirect(url_for("dashboard"))


@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    try:
        account_id = int(request.form.get("account_id", ""))
        amount = parse_money(request.form.get("amount"))
    except (ValueError, TypeError):
        flash("Please select an account and enter a valid withdrawal amount.", "danger")
        return redirect(url_for("dashboard"))

    conn = cursor = None
    try:
        conn = get_db()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        account = owned_active_account(cursor, account_id, session["customer_id"], lock=True)
        if not account:
            conn.rollback()
            flash("Account not found or inactive.", "danger")
            return redirect(url_for("dashboard"))
        if Decimal(str(account["balance"])) < amount:
            conn.rollback()
            flash("Insufficient balance. No money was withdrawn.", "danger")
            return redirect(url_for("dashboard"))
        cursor.execute(
            "UPDATE accounts SET balance = balance - %s WHERE account_id = %s AND balance >= %s",
            (amount, account_id, amount),
        )
        if cursor.rowcount != 1:
            conn.rollback()
            flash("Withdrawal could not be completed. Please try again.", "danger")
            return redirect(url_for("dashboard"))
        cursor.execute(
            """INSERT INTO transactions
               (from_account_id, to_account_id, transaction_type, amount, reference_code, description)
               VALUES (%s, NULL, 'WITHDRAWAL', %s, %s, 'Demo cash withdrawal')""",
            (account_id, amount, new_reference()),
        )
        conn.commit()
        flash(f"Demo withdrawal of ₹{amount:,.2f} completed.", "success")
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        close_db(conn, cursor)
    return redirect(url_for("dashboard"))


@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    if request.method == "GET":
        conn = cursor = None
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            accounts = fetch_customer_accounts(cursor, session["customer_id"])
            cursor.execute(
                """SELECT b.beneficiary_id, b.nickname, a.account_number, c.full_name AS account_holder
                   FROM beneficiaries b
                   JOIN accounts a ON a.account_id = b.beneficiary_account_id
                   JOIN customers c ON c.customer_id = a.customer_id
                   WHERE b.customer_id = %s ORDER BY b.beneficiary_id DESC""",
                (session["customer_id"],),
            )
            beneficiaries = cursor.fetchall()
            return render_template("transfer.html", accounts=accounts, beneficiaries=beneficiaries)
        finally:
            close_db(conn, cursor)

    try:
        source_id = int(request.form.get("source_account_id", ""))
        destination_number = request.form.get("destination_account_number", "").strip()
        amount = parse_money(request.form.get("amount"))
    except (ValueError, TypeError):
        flash("Please select a source account and enter a valid amount.", "danger")
        return redirect(url_for("transfer"))

    conn = cursor = None
    try:
        conn = get_db()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        source = owned_active_account(cursor, source_id, session["customer_id"], lock=False)
        cursor.execute(
            """SELECT account_id, account_number, customer_id, balance, status
               FROM accounts WHERE account_number = %s AND status = 'ACTIVE'""",
            (destination_number,),
        )
        destination_unlocked = cursor.fetchone()
        if not source or not destination_unlocked:
            conn.rollback()
            flash("Source or destination account was not found or is inactive.", "danger")
            return redirect(url_for("transfer"))
        destination_id = destination_unlocked["account_id"]
        if source_id == destination_id:
            conn.rollback()
            flash("Source and destination accounts must be different.", "danger")
            return redirect(url_for("transfer"))

        # Lock both accounts in consistent ID order to reduce deadlock risk.
        ordered_ids = sorted([source_id, destination_id])
        cursor.execute(
            """SELECT account_id, account_number, customer_id, balance, status
               FROM accounts WHERE account_id IN (%s, %s) ORDER BY account_id FOR UPDATE""",
            (ordered_ids[0], ordered_ids[1]),
        )
        locked_rows = {row["account_id"]: row for row in cursor.fetchall()}
        locked_source = locked_rows.get(source_id)
        locked_destination = locked_rows.get(destination_id)
        if (
            not locked_source or not locked_destination
            or locked_source["status"] != "ACTIVE"
            or locked_destination["status"] != "ACTIVE"
        ):
            conn.rollback()
            flash("An account became unavailable. Please try again.", "danger")
            return redirect(url_for("transfer"))
        if Decimal(str(locked_source["balance"])) < amount:
            conn.rollback()
            flash("Insufficient balance. No transfer was made.", "danger")
            return redirect(url_for("transfer"))

        cursor.execute(
            "UPDATE accounts SET balance = balance - %s WHERE account_id = %s AND balance >= %s",
            (amount, source_id, amount),
        )
        if cursor.rowcount != 1:
            conn.rollback()
            flash("Transfer could not be completed. Please try again.", "danger")
            return redirect(url_for("transfer"))
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s", (amount, destination_id))
        reference = new_reference()
        cursor.execute(
            """INSERT INTO transactions
               (from_account_id, to_account_id, transaction_type, amount, reference_code, description)
               VALUES (%s, %s, 'TRANSFER', %s, %s, %s)""",
            (source_id, destination_id, amount, reference, f"Transfer to {destination_number}"),
        )
        conn.commit()
        flash(f"Transfer of ₹{amount:,.2f} successful. Reference: {reference}", "success")
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        close_db(conn, cursor)
    return redirect(url_for("dashboard"))


@app.route("/beneficiaries", methods=["GET", "POST"])
@login_required
def beneficiaries():
    conn = cursor = None
    if request.method == "POST":
        account_number = request.form.get("account_number", "").strip()
        nickname = request.form.get("nickname", "").strip()[:50]
        try:
            conn = get_db()
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT account_id, customer_id FROM accounts WHERE account_number = %s AND status = 'ACTIVE'",
                (account_number,),
            )
            account = cursor.fetchone()
            if not account:
                conn.rollback()
                flash("No active account found with that number.", "danger")
            elif account["customer_id"] == session["customer_id"]:
                conn.rollback()
                flash("You cannot add your own account as a beneficiary.", "warning")
            else:
                cursor.execute(
                    "INSERT INTO beneficiaries (customer_id, beneficiary_account_id, nickname) VALUES (%s, %s, %s)",
                    (session["customer_id"], account["account_id"], nickname or "Recipient"),
                )
                conn.commit()
                flash("Beneficiary added.", "success")
        except mysql.connector.IntegrityError:
            if conn:
                conn.rollback()
            flash("This beneficiary is already saved.", "warning")
        finally:
            close_db(conn, cursor)
        return redirect(url_for("beneficiaries"))

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT b.beneficiary_id, b.nickname, a.account_number, c.full_name AS account_holder
               FROM beneficiaries b
               JOIN accounts a ON a.account_id = b.beneficiary_account_id
               JOIN customers c ON c.customer_id = a.customer_id
               WHERE b.customer_id = %s ORDER BY b.beneficiary_id DESC""",
            (session["customer_id"],),
        )
        saved_beneficiaries = cursor.fetchall()
        return render_template("beneficiaries.html", beneficiaries=saved_beneficiaries)
    finally:
        close_db(conn, cursor)


@app.route("/beneficiaries/<int:beneficiary_id>/delete", methods=["POST"])
@login_required
def delete_beneficiary(beneficiary_id):
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM beneficiaries WHERE beneficiary_id = %s AND customer_id = %s",
            (beneficiary_id, session["customer_id"]),
        )
        conn.commit()
        if cursor.rowcount:
            flash("Beneficiary removed.", "success")
        else:
            flash("Beneficiary not found.", "warning")
    finally:
        close_db(conn, cursor)
    return redirect(url_for("beneficiaries"))


@app.route("/transactions")
@login_required
def transactions_page():
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        rows = fetch_customer_transactions(cursor, session["customer_id"], 100)
        return render_template("transactions.html", transactions=rows)
    finally:
        close_db(conn, cursor)


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=getattr(error, "description", "Bad request.")), 400


@app.errorhandler(mysql.connector.Error)
def database_error(error):
    # Log details to the server terminal but avoid exposing DB credentials or SQL to users.
    app.logger.error("Database operation failed: %s", error)
    return render_template(
        "error.html", code=503,
        message="The database could not complete the request. Check that MySQL is running, the schema is imported, and your .env settings are correct.",
    ), 503


if __name__ == "__main__":
    # Debug mode is convenient for local college projects. Do not use it in production.
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "1") == "1")

