import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="phonebook_db",
        user="postgres",
        password="500191" 
    )
    return conn