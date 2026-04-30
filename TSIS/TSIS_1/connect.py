# ============================================================
#  connect.py  —  Returns a live psycopg2 connection
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_connection():
    """Return a psycopg2 connection to the phonebook database."""
    return psycopg2.connect(
        host     = DB_HOST,
        port     = DB_PORT,
        dbname   = DB_NAME,
        user     = DB_USER,
        password = DB_PASSWORD
    )
