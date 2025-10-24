"""
Upload inventory data to PostgreSQL database on Railway
"""
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict
import os


def upload_inventory_to_postgres(
    inventory_data: List[Dict],
    database_url: str = None
) -> int:
    """
    Upload inventory data to PostgreSQL database on Railway.

    Args:
        inventory_data: List of inventory records from scraper
        database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)

    Returns:
        Number of records uploaded

    Raises:
        psycopg2.Error: If database operation fails
    """
    if database_url is None:
        database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        raise ValueError("DATABASE_URL not provided and not found in environment")

    conn = None
    cursor = None

    try:
        # Connect to PostgreSQL
        print(f"Connecting to PostgreSQL database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Prepare data for insertion
        # Map fields to match database schema
        records = []
        for item in inventory_data:
            record = (
                item.get('key'),              # key (primary key)
                item.get('gl_group'),         # gl_group
                item.get('type'),             # type
                item.get('qty'),              # qty
                item.get('unit'),             # unit
                item.get('actual_unit_cost'), # actual_unit_cost
                item.get('actual_value'),     # actual_value
                item.get('date'),             # date
                item.get('area'),             # area
                item.get('item')              # item
            )
            records.append(record)

        # Use INSERT ... ON CONFLICT to handle duplicates (upsert)
        upsert_query = """
            INSERT INTO inventory_cost (
                key, gl_group, type, qty, unit,
                actual_unit_cost, actual_value, date, area, item
            )
            VALUES %s
            ON CONFLICT (key)
            DO UPDATE SET
                gl_group = EXCLUDED.gl_group,
                type = EXCLUDED.type,
                qty = EXCLUDED.qty,
                unit = EXCLUDED.unit,
                actual_unit_cost = EXCLUDED.actual_unit_cost,
                actual_value = EXCLUDED.actual_value,
                date = EXCLUDED.date,
                area = EXCLUDED.area,
                item = EXCLUDED.item
        """

        print(f"Uploading {len(records)} records to database...")
        execute_values(cursor, upsert_query, records)

        # Commit the transaction
        conn.commit()
        print(f"Successfully uploaded {len(records)} records")

        return len(records)

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"Database error: {e}")
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error uploading to PostgreSQL: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def test_connection(database_url: str = None) -> bool:
    """
    Test database connection.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        True if connection successful, False otherwise
    """
    if database_url is None:
        database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("DATABASE_URL not provided")
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Connected to PostgreSQL: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection
    print("Testing database connection...")
    test_connection()
