from app.database import get_db_connection


def initialize_customer_table():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        INSERT INTO customers (name, email)
        VALUES
            ('Rahul Kumar', 'rahul@example.com'),
            ('Priya Sharma', 'priya@example.com'),
            ('Gopi Reddy', 'gopi@example.com')
        ON CONFLICT (email) DO NOTHING
    """)

    connection.commit()
    cursor.close()
    connection.close()


def search_customers(search_term):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email
        FROM customers
        WHERE name ILIKE %s
           OR email ILIKE %s
        ORDER BY id
    """, (f"%{search_term}%", f"%{search_term}%"))

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2]
        }
        for row in rows
    ]
