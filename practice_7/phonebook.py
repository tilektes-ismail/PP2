import psycopg2
import csv
from TSIS.TSIS_1.connect import get_connection

# 1. Insert from CSV
def insert_from_csv():
    conn = get_connection()
    cur = conn.cursor()

    with open("contacts.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                "INSERT INTO contacts (first_name, username, phone) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
                (row["first_name"], row["username"], row["phone"])
            )

    conn.commit()
    cur.close()
    conn.close()
    print("Done! Contacts loaded from CSV.")


# 2. Insert from console
def insert_from_console():
    name  = input("First name: ")
    user  = input("Username: ")
    phone = input("Phone: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO contacts (first_name, username, phone) VALUES (%s, %s, %s)",
        (name, user, phone)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Contact added!")


# 3. Update contact
def update_contact():
    user  = input("Username to update: ")
    name  = input("New first name: ")
    phone = input("New phone: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE contacts SET first_name = %s, phone = %s WHERE username = %s",
        (name, phone, user)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Contact updated!")


# 4. Search contacts
def search_contacts():
    print("1. By name")
    print("2. By phone prefix")
    choice = input("Choose: ")

    conn = get_connection()
    cur = conn.cursor()

    if choice == "1":
        name = input("Enter name: ")
        cur.execute("SELECT * FROM contacts WHERE first_name ILIKE %s", (f"%{name}%",))
    elif choice == "2":
        prefix = input("Enter phone prefix: ")
        cur.execute("SELECT * FROM contacts WHERE phone LIKE %s", (f"{prefix}%",))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
        for row in rows:
            print(row)
    else:
        print("No contacts found.")


# 5. Delete contact
def delete_contact():
    print("1. By username")
    print("2. By phone")
    choice = input("Choose: ")

    conn = get_connection()
    cur = conn.cursor()

    if choice == "1":
        user = input("Enter username: ")
        cur.execute("DELETE FROM contacts WHERE username = %s", (user,))
    elif choice == "2":
        phone = input("Enter phone: ")
        cur.execute("DELETE FROM contacts WHERE phone = %s", (phone,))

    conn.commit()
    cur.close()
    conn.close()
    print("Contact deleted!")


# Main menu
def main():
    while True:
        print("\n=== PhoneBook ===")
        print("1. Load from CSV")
        print("2. Add contact")
        print("3. Update contact")
        print("4. Search contacts")
        print("5. Delete contact")
        print("0. Exit")

        choice = input("Choose: ")

        if choice == "1":
            insert_from_csv()
        elif choice == "2":
            insert_from_console()
        elif choice == "3":
            update_contact()
        elif choice == "4":
            search_contacts()
        elif choice == "5":
            delete_contact()
        elif choice == "0":
            break

main()