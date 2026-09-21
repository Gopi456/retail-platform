import os
import psycopg2


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "retaildb"),
        user=os.getenv("DB_USER", "retailuser"),
        password=os.getenv("DB_PASSWORD", "retailpass")
    )