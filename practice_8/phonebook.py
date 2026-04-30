import psycopg2
import csv
from TSIS.TSIS_1.connect import get_connection


# ── 1. Search contacts using DB function (pattern on name/username/phone) ─────
def search_contacts():
    pattern = input("Enter search pattern (name, username, or phone part): ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM search_contacts(%s)", (pattern,))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    if rows:
        print(f"\n{'ID':<5} {'First Name':<15} {'Username':<15} {'Phone':<15}")
        print("-" * 52)
        for row in rows:
            print(f"{str(row[0]):<5} {str(row[1] or ''):<15} {str(row[2] or ''):<15} {str(row[3] or ''):<15}")
    else:
        print("No contacts found.")


# ── 2. Upsert contact (insert or update phone) using DB procedure ──────────────
def upsert_contact():
    name  = input("First name: ")
    user  = input("Username: ")
    phone = input("Phone: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("CALL upsert_contact(%s, %s, %s)", (name, user, phone))

    conn.commit()
    cur.close()
    conn.close()
    print("Done! Contact inserted or updated.")


# ── 3. Insert many contacts from console (loop) using DB procedure ─────────────
def insert_many_contacts():
    print("Enter contacts one by one. Type 'done' as first name to finish.\n")

    first_names = []
    usernames   = []
    phones      = []

    while True:
        name = input("First name (or 'done'): ")
        if name.lower() == "done":
            break
        user  = input("Username: ")
        phone = input("Phone: ")
        first_names.append(name)
        usernames.append(user)
        phones.append(phone)

    if not first_names:
        print("No contacts entered.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "CALL insert_many_contacts(%s::varchar[], %s::varchar[], %s::varchar[])",
        (first_names, usernames, phones)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Batch insert complete. Check server notices for any invalid records.")


# ── 4. Paginated listing using DB function ─────────────────────────────────────
def list_paginated():
    try:
        limit  = int(input("Records per page: "))
        page   = int(input("Page number (starting from 1): "))
    except ValueError:
        print("Please enter valid numbers.")
        return

    offset = (page - 1) * limit

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM get_contacts_paginated(%s, %s)", (limit, offset))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    if rows:
        print(f"\nPage {page}  (limit={limit}, offset={offset})")
        print(f"{'ID':<5} {'First Name':<15} {'Username':<15} {'Phone':<15}")
        print("-" * 52)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<15} {row[2]:<15} {row[3]:<15}")
    else:
        print("No records on this page.")


# ── 5. Delete contact using DB procedure ───────────────────────────────────────
def delete_contact():
    print("Delete by:")
    print("1. Username")
    print("2. Phone")
    choice = input("Choose: ")

    conn = get_connection()
    cur = conn.cursor()

    if choice == "1":
        user = input("Enter username: ")
        cur.execute("CALL delete_contact(p_username => %s)", (user,))
    elif choice == "2":
        phone = input("Enter phone: ")
        cur.execute("CALL delete_contact(p_phone => %s)", (phone,))
    else:
        print("Invalid choice.")
        conn.close()
        return

    conn.commit()
    cur.close()
    conn.close()
    print("Contact deleted (if it existed).")


# ── Load from CSV (kept from Practice 7) ──────────────────────────────────────
def insert_from_csv():
    conn = get_connection()
    cur = conn.cursor()

    with open("/Users/beka/PP2/practice_7/contacts.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                "INSERT INTO contacts (first_name, username, phone) "
                "VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
                (row["first_name"], row["username"], row["phone"])
            )

    conn.commit()
    cur.close()
    conn.close()
    print("Contacts loaded from CSV.")


# ── Main menu ──────────────────────────────────────────────────────────────────
def main():
    while True:
        print("\n=== PhoneBook (Practice 8) ===")
        print("1. Load from CSV")
        print("2. Add / update one contact (upsert)")
        print("3. Batch insert contacts")
        print("4. Search contacts")
        print("5. List contacts (paginated)")
        print("6. Delete contact")
        print("0. Exit")

        choice = input("Choose: ")

        if   choice == "1": insert_from_csv()
        elif choice == "2": upsert_contact()
        elif choice == "3": insert_many_contacts()
        elif choice == "4": search_contacts()
        elif choice == "5": list_paginated()
        elif choice == "6": delete_contact()
        elif choice == "0": break
        else: print("Invalid option, try again.")


main()
