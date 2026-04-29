# ============================================================
#  phonebook.py  —  PhoneBook TSIS1
#
#  Practice 7 & 8 features (already implemented, kept as-is):
#    - CRUD, CSV import, console entry, update, delete
#    - Pattern search, upsert, bulk insert, pagination, delete proc
#
#  NEW in TSIS1 (3.1 – 3.4):
#    3.1  Extended schema: phones table, groups table, email, birthday
#    3.2  Filter by group, search by email, sort, paginated navigation
#    3.3  Export to JSON, import from JSON, extended CSV import
#    3.4  Procedures: add_phone, move_to_group
#         Function:   search_contacts (email + all phones)
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csv
import json
from connect import get_connection


# ============================================================
#  Helpers
# ============================================================

def _print_contacts(rows, headers=None):
    """Pretty-print contact rows."""
    if not rows:
        print("  (no results)")
        return
    if headers is None:
        headers = ["ID", "First", "Last", "Email", "Birthday", "Group"]
    widths = [5, 12, 12, 22, 12, 10]
    fmt = "".join(f"{{:<{w}}}" for w in widths)
    print("\n  " + fmt.format(*headers))
    print("  " + "-" * sum(widths))
    for r in rows:
        print("  " + fmt.format(*[str(x) if x is not None else "" for x in r]))


def _run_schema_and_procedures(conn):
    """Execute schema.sql and procedures.sql on first run."""
    base = os.path.dirname(os.path.abspath(__file__))
    cur  = conn.cursor()
    for fname in ("schema.sql", "procedures.sql"):
        fpath = os.path.join(base, fname)
        if os.path.exists(fpath):
            with open(fpath, encoding="utf-8") as f:
                cur.execute(f.read())
    conn.commit()
    cur.close()


# ============================================================
#  Setup — run schema + procedures once
# ============================================================

def setup():
    """Create tables and register all stored procedures/functions."""
    conn = get_connection()
    _run_schema_and_procedures(conn)
    conn.close()
    print("Schema and procedures are ready.")


# ============================================================
#  Practice 7 — kept exactly, updated for new schema
# ============================================================

def insert_from_csv(filepath="contacts.csv"):
    """Extended CSV import: handles email, birthday, group, phone_type."""
    conn = get_connection()
    cur  = conn.cursor()
    inserted = 0
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get or create group
            group_id = None
            if row.get('group'):
                cur.execute(
                    "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id;",
                    (row['group'],)
                )
                group_id = cur.fetchone()[0]

            # Insert contact
            cur.execute("""
                INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id;
            """, (row['first_name'], row.get('last_name'), row.get('email'),
                  row.get('birthday') or None, group_id))
            result = cur.fetchone()
            if result:
                contact_id = result[0]
                # Insert phone into phones table
                if row.get('phone'):
                    cur.execute("""
                        INSERT INTO phones (contact_id, phone, type)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (contact_id, row['phone'], row.get('phone_type', 'mobile')))
                inserted += 1
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {inserted} contacts from CSV.")


def insert_from_console():
    """Add one contact from console input."""
    print("\n--- Add New Contact ---")
    first_name = input("First name  : ").strip()
    last_name  = input("Last name   : ").strip()
    email      = input("Email       : ").strip()
    birthday   = input("Birthday (YYYY-MM-DD, or blank): ").strip() or None
    phone      = input("Phone       : ").strip()
    phone_type = input("Phone type (home/work/mobile): ").strip() or 'mobile'

    # Show available groups
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, name FROM groups ORDER BY id;")
    groups = cur.fetchall()
    print("Groups: " + ", ".join(f"{g[0]}={g[1]}" for g in groups))
    group_id = input("Group ID (or blank): ").strip() or None

    try:
        cur.execute("""
            INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (first_name, last_name or None, email or None, birthday, group_id))
        contact_id = cur.fetchone()[0]
        if phone:
            cur.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s);",
                (contact_id, phone, phone_type)
            )
        conn.commit()
        print(f"Contact '{first_name}' added.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()


def update_contact():
    """Update first name or a phone number by contact ID."""
    print("\n--- Update Contact ---")
    try:
        cid = int(input("Contact ID to update: ").strip())
    except ValueError:
        print("Invalid ID.")
        return
    print("  1. Update first name\n  2. Update a phone number")
    choice = input("Choice (1/2): ").strip()
    conn = get_connection()
    cur  = conn.cursor()
    try:
        if choice == '1':
            val = input("New first name: ").strip()
            cur.execute("UPDATE contacts SET first_name=%s WHERE id=%s;", (val, cid))
        elif choice == '2':
            old = input("Old phone number: ").strip()
            new = input("New phone number: ").strip()
            cur.execute("UPDATE phones SET phone=%s WHERE contact_id=%s AND phone=%s;", (new, cid, old))
        else:
            print("Invalid choice.")
            return
        conn.commit()
        print("Updated." if cur.rowcount else "Nothing found to update.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()


def delete_contact():
    """Delete by first name or phone — calls the Practice 8 procedure."""
    print("\n--- Delete Contact ---")
    print("  1. Delete by first name\n  2. Delete by phone")
    choice = input("Choice (1/2): ").strip()
    conn = get_connection()
    cur  = conn.cursor()
    try:
        if choice == '1':
            val = input("First name: ").strip()
            cur.execute("DELETE FROM contacts WHERE first_name ILIKE %s;", (val,))
        elif choice == '2':
            val = input("Phone: ").strip()
            cur.execute("DELETE FROM phones WHERE phone=%s;", (val,))
        else:
            print("Invalid choice.")
            return
        conn.commit()
        print(f"Deleted {cur.rowcount} record(s).")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()


# ============================================================
#  3.2 — Advanced Console Search & Filter
# ============================================================

def filter_by_group():
    """Show contacts belonging to a selected group."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, name FROM groups ORDER BY id;")
    groups = cur.fetchall()
    print("\n--- Filter by Group ---")
    for g in groups:
        print(f"  {g[0]}. {g[1]}")
    try:
        gid = int(input("Group ID: ").strip())
    except ValueError:
        print("Invalid ID.")
        cur.close(); conn.close(); return

    cur.execute("""
        SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        WHERE c.group_id = %s
        ORDER BY c.first_name;
    """, (gid,))
    _print_contacts(cur.fetchall())
    cur.close()
    conn.close()


def search_by_email():
    """Partial email match search."""
    print("\n--- Search by Email ---")
    pattern = input("Email pattern (e.g. gmail): ").strip()
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        WHERE c.email ILIKE %s
        ORDER BY c.first_name;
    """, (f'%{pattern}%',))
    _print_contacts(cur.fetchall())
    cur.close()
    conn.close()


def sorted_search():
    """Search all contacts and sort by name, birthday, or date added."""
    print("\n--- Sorted Contact List ---")
    print("  Sort by:  1=Name  2=Birthday  3=Date Added")
    choice = input("Choice (1/2/3): ").strip()
    order  = {"1": "c.first_name", "2": "c.birthday", "3": "c.created_at"}.get(choice, "c.first_name")
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER BY {order};
    """)
    _print_contacts(cur.fetchall())
    cur.close()
    conn.close()


def paginated_navigation():
    """Navigate contacts page by page."""
    print("\n--- Paginated Navigation ---")
    try:
        limit = int(input("Rows per page: ").strip())
    except ValueError:
        print("Invalid number.")
        return

    page = 1
    while True:
        offset = (page - 1) * limit
        conn = get_connection()
        cur  = conn.cursor()

        # Query from the NEW contacts + phones + groups tables
        cur.execute("""
            SELECT
                c.id,
                c.first_name,
                c.last_name,
                c.email,
                c.birthday,
                g.name  AS group_name,
                STRING_AGG(p.phone || ' (' || COALESCE(p.type, '?') || ')', ', ') AS phones
            FROM contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            LEFT JOIN phones p ON p.contact_id = c.id
            GROUP BY c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
            ORDER BY c.id
            LIMIT %s OFFSET %s;
        """, (limit, offset))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        print(f"\n  --- Page {page} ---")
        if rows:
            print(f"  {'ID':<5} {'First':<12} {'Last':<12} {'Email':<22} {'Birthday':<12} {'Group':<10} {'Phones'}")
            print("  " + "-" * 90)
            for r in rows:
                print(f"  {r[0]:<5} {str(r[1] or ''):<12} {str(r[2] or ''):<12} {str(r[3] or ''):<22} {str(r[4] or ''):<12} {str(r[5] or ''):<10} {str(r[6] or '')}")
        else:
            print("  (no more results)")

        cmd = input("\n  [next / prev / quit]: ").strip().lower()
        if cmd == 'next':
            if rows:
                page += 1
            else:
                print("  Already at last page.")
        elif cmd == 'prev':
            page = max(1, page - 1)
        elif cmd == 'quit':
            break3


# ============================================================
#  3.3 — Import / Export
# ============================================================

def export_to_json(filepath="contacts_export.json"):
    """Export all contacts with phones and group to a JSON file."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT c.id, c.first_name, c.last_name, c.email,
               c.birthday::TEXT, g.name AS group_name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER BY c.id;
    """)
    contacts = cur.fetchall()

    output = []
    for row in contacts:
        cid = row[0]
        # Fetch all phones for this contact
        cur.execute("SELECT phone, type FROM phones WHERE contact_id=%s;", (cid,))
        phones = [{"phone": p[0], "type": p[1]} for p in cur.fetchall()]
        output.append({
            "id":         cid,
            "first_name": row[1],
            "last_name":  row[2],
            "email":      row[3],
            "birthday":   row[4],
            "group":      row[5],
            "phones":     phones
        })

    cur.close()
    conn.close()

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(output)} contacts to '{filepath}'.")


def import_from_json(filepath="contacts_export.json"):
    """Import contacts from JSON. On duplicate name, ask skip or overwrite."""
    if not os.path.exists(filepath):
        print(f"File '{filepath}' not found.")
        return

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    conn = get_connection()
    cur  = conn.cursor()
    inserted = updated = skipped = 0

    for c in data:
        # Check if a contact with same first+last name already exists
        cur.execute("""
            SELECT id FROM contacts
            WHERE first_name ILIKE %s AND last_name ILIKE %s;
        """, (c.get('first_name', ''), c.get('last_name', '') or ''))
        existing = cur.fetchone()

        if existing:
            print(f"  Duplicate: {c['first_name']} {c.get('last_name','')}")
            action = input("  Skip (s) or Overwrite (o)? ").strip().lower()
            if action == 'o':
                # Get group id
                group_id = None
                if c.get('group'):
                    cur.execute(
                        "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id;",
                        (c['group'],)
                    )
                    group_id = cur.fetchone()[0]
                cur.execute("""
                    UPDATE contacts SET email=%s, birthday=%s, group_id=%s
                    WHERE id=%s;
                """, (c.get('email'), c.get('birthday'), group_id, existing[0]))
                # Replace phones
                cur.execute("DELETE FROM phones WHERE contact_id=%s;", (existing[0],))
                for p in c.get('phones', []):
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s);",
                        (existing[0], p['phone'], p.get('type','mobile'))
                    )
                updated += 1
            else:
                skipped += 1
        else:
            # Get or create group
            group_id = None
            if c.get('group'):
                cur.execute(
                    "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id;",
                    (c['group'],)
                )
                group_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                VALUES (%s,%s,%s,%s,%s) RETURNING id;
            """, (c['first_name'], c.get('last_name'), c.get('email'),
                  c.get('birthday'), group_id))
            cid = cur.fetchone()[0]
            for p in c.get('phones', []):
                cur.execute(
                    "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s);",
                    (cid, p['phone'], p.get('type','mobile'))
                )
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Import done — inserted: {inserted}, overwritten: {updated}, skipped: {skipped}.")


# ============================================================
#  3.4 — New Stored Procedures (called from Python)
# ============================================================

def add_phone():
    """Call the add_phone procedure to add a phone to an existing contact."""
    print("\n--- Add Phone to Contact ---")
    name  = input("Contact first name : ").strip()
    phone = input("Phone number       : ").strip()
    ptype = input("Type (home/work/mobile): ").strip() or 'mobile'
    conn  = get_connection()
    cur   = conn.cursor()
    try:
        cur.execute("CALL add_phone(%s, %s, %s);", (name, phone, ptype))
        conn.commit()
        print("Phone added.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()


def move_to_group():
    """Call the move_to_group procedure to reassign a contact's group."""
    print("\n--- Move Contact to Group ---")
    name  = input("Contact first name : ").strip()
    group = input("New group name     : ").strip()
    conn  = get_connection()
    cur   = conn.cursor()
    try:
        cur.execute("CALL move_to_group(%s, %s);", (name, group))
        conn.commit()
        print(f"Moved '{name}' to group '{group}'.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()


def search_contacts():
    """Call the search_contacts function — matches name, email, all phones."""
    print("\n--- Search Contacts (name / email / phone) ---")
    query = input("Search query: ").strip()
    conn  = get_connection()
    cur   = conn.cursor()
    cur.execute("SELECT * FROM search_contacts(%s);", (query,))
    rows  = cur.fetchall()
    cur.close()
    conn.close()
    _print_contacts(rows)


# ============================================================
#  Main Menu
# ============================================================

def main():
    setup()   # create tables + register all procedures/functions

    while True:
        print("\n========== PhoneBook TSIS1 ==========")
        print("  --- Data Entry ---")
        print("  1. Import contacts from CSV")
        print("  2. Add one contact manually")
        print("  3. Update a contact")
        print("  4. Delete a contact")
        print("  --- Search & Filter ---")
        print("  5. Search contacts (name/email/phone)")
        print("  6. Filter by group")
        print("  7. Search by email")
        print("  8. Sorted contact list")
        print("  9. Browse with pagination")
        print("  --- Phone & Group ---")
        print("  10. Add phone to contact")
        print("  11. Move contact to group")
        print("  --- Import / Export ---")
        print("  12. Export contacts to JSON")
        print("  13. Import contacts from JSON")
        print("  0.  Exit")
        print("=====================================")
        choice = input("Choose an option: ").strip()

        if   choice == '1':  insert_from_csv()
        elif choice == '2':  insert_from_console()
        elif choice == '3':  update_contact()
        elif choice == '4':  delete_contact()
        elif choice == '5':  search_contacts()
        elif choice == '6':  filter_by_group()
        elif choice == '7':  search_by_email()
        elif choice == '8':  sorted_search()
        elif choice == '9':  paginated_navigation()
        elif choice == '10': add_phone()
        elif choice == '11': move_to_group()
        elif choice == '12': export_to_json()
        elif choice == '13': import_from_json()
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
