import psycopg2
import csv
from config import DB_CONFIG

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_table():
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
    with get_connection() as conn:
        with conn.cursor() as cur:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if not row: continue
                    if len(row) == 4:
                        data = (row[1], row[2], row[3])
                    elif len(row) == 3:
                        data = (row[0], row[1], row[2])
                    else:
                        print(f"Skipping invalid row: {row}")
                        continue
                    cur.execute(
                        "INSERT INTO contacts (first_name, last_name, phone_number) VALUES (%s, %s, %s)",
                        data
                    )
            conn.commit()

def add_contact(first, last, phone):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO contacts (first_name, last_name, phone_number) VALUES (%s, %s, %s)", (first, last, phone))
            conn.commit()
    print(f"✅ Contact '{first} {last}' added successfully!")

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
    print(f"✅ Contact ID {contact_id} updated successfully!")

def delete_contact(contact_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
            conn.commit()
    print(f"✅ Contact ID {contact_id} deleted successfully!")

def search_contacts(name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM search_contact_by_name(%s)", (name,))
            return cur.fetchall()

def print_contacts(contacts):
    if not contacts:
        print("No contacts found.")
    else:
        print("\n" + "-" * 50)
        for c in contacts:
            print(f"ID: {c[0]} | Name: {c[1]} {c[2]} | Phone: {c[3]}")
        print("-" * 50)

# ── MENU ──────────────────────────────────────────
def menu():
    create_table()  # Make sure table exists on startup

    while True:
        print("""
========== PHONEBOOK MENU ==========
1. View all contacts
2. Add a contact
3. Update a contact's phone number
4. Delete a contact
5. Search contact by name
0. Exit
=====================================""")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            contacts = get_all_contacts()
            print_contacts(contacts)

        elif choice == "2":
            first = input("First name: ").strip()
            last  = input("Last name: ").strip()
            phone = input("Phone number: ").strip()
            add_contact(first, last, phone)

        elif choice == "3":
            print_contacts(get_all_contacts())
            contact_id = input("Enter the ID of the contact to update: ").strip()
            new_phone  = input("Enter the new phone number: ").strip()
            update_contact_phone(int(contact_id), new_phone)

        elif choice == "4":
            print_contacts(get_all_contacts())
            contact_id = input("Enter the ID of the contact to delete: ").strip()
            confirm = input(f"Are you sure you want to delete ID {contact_id}? (y/n): ").strip().lower()
            if confirm == "y":
                delete_contact(int(contact_id))
            else:
                print("Cancelled.")

        elif choice == "5":
            name = input("Enter name to search: ").strip()
            results = search_contacts(name)
            print_contacts(results)


        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("❌ Invalid option. Please choose a number from the menu.")

if __name__ == "__main__":
    menu()