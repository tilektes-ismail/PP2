# connect.py
from phonebook import create_table, import_from_csv, get_all_contacts, add_contact

def main():
    try:
        # 1. Setup
        create_table()
        print("Table ready.")

        # 2. Import CSV
        import_from_csv('contacts.csv')
        print("CSV data imported.")

        # 3. Add a manual contact (CRUD: Create)
        add_contact("Salah", "Egyptian King", "000-111-2222")
        
        # 4. Show results (CRUD: Read)
        print("\n--- Current Phonebook Contents ---")
        for contact in get_all_contacts():
            print(f"ID: {contact[0]} | Name: {contact[1]} {contact[2]} | Phone: {contact[3]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()