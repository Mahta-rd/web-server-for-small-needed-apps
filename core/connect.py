import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """
    Context manager for database connections
    """
    conn = sqlite3.connect('database.db')
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None):
    """
    Execute a query and return results
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()