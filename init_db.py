"""Initialize the hosted MySQL schema before starting the demo app.

This is safe to run on every Render start: schema.sql uses CREATE IF NOT EXISTS
and CREATE OR REPLACE VIEW, and does not drop or truncate application data.
"""
import os
from pathlib import Path

import mysql.connector


DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "database": "defaultdb",
    "charset": "utf8mb4",
    "use_unicode": True,
}

ssl_ca = os.getenv("DB_SSL_CA")
if ssl_ca:
    DB_CONFIG.update(
        ssl_ca=ssl_ca,
        ssl_verify_cert=True,
        ssl_verify_identity=True,
    )


def main():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    try:
        for statement in schema.split(";"):
            if statement.strip():
                cursor.execute(statement)
        connection.commit()
        print("Database schema is ready.")
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
