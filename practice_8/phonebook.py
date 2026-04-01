import psycopg2
import csv
from config import DB_CONFIG

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_table():
    """Criteria: Create table in PostgreSQL"""
    query = """
    CREATE TABLE IF NOT EXISTS contacts (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        phone_number VARCHAR(20)
    );
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()

def import_from_csv(file_path):
    """Criteria: Import data from CSV file"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if not row: continue # Skip empty lines
                    
                    # Logic to handle both 3-column and 4-column CSVs
                    if len(row) == 4: # ID, First, Last, Phone
                        data = (row[1], row[2], row[3])
                    elif len(row) == 3: # First, Last, Phone
                        data = (row[0], row[1], row[2])
                    else:
                        print(f"Skipping invalid row: {row}")
                        continue
                        
                    cur.execute(
                        "INSERT INTO contacts (first_name, last_name, phone_number) VALUES (%s, %s, %s)",
                        data
                    )
            conn.commit()

# CRUD Operations
def add_contact(first, last, phone):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO contacts (first_name, last_name, phone_number) VALUES (%s, %s, %s)", (first, last, phone))
            conn.commit()

def get_all_contacts():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM contacts ORDER BY id ASC;")
            return cur.fetchall()

def update_contact_phone(contact_id, new_phone):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE contacts SET phone_number = %s WHERE id = %s", (new_phone, contact_id))
            conn.commit()

def delete_contact(contact_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
            conn.commit()

def add_contact_proc(first, last, phone):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Use 'CALL' for procedures
            cur.execute("CALL add_new_contact(%s, %s, %s)", (first, last, phone))
            # No need for conn.commit() if the procedure has it internally

def search_contacts(name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Use 'SELECT' for functions
            cur.execute("SELECT * FROM search_contact_by_name(%s)", (name,))
            return cur.fetchall()