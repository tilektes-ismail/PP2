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

import sys, os                                              # sys for path manipulation, os for file paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Add this file's folder to module search path so connect.py is found

import csv      # Built-in CSV reader for parsing contact import files
import json     # Built-in JSON library for export/import functionality
from connect import get_connection  # Our own DB helper that returns a psycopg2 connection


# ============================================================
#  Helpers
# ============================================================

def _print_contacts(rows, headers=None):
    """Pretty-print contact rows."""
    if not rows:                    # Nothing to display — print a placeholder and stop
        print("  (no results)")
        return
    if headers is None:             # Use default column headers if none were passed in
        headers = ["ID", "First", "Last", "Email", "Birthday", "Group"]
    widths = [5, 12, 12, 22, 12, 10]                        # Fixed column widths in characters
    fmt = "".join(f"{{:<{w}}}" for w in widths)             # Build a left-aligned format string from widths
    print("\n  " + fmt.format(*headers))                    # Print header row with 2-space indent
    print("  " + "-" * sum(widths))                         # Print a separator line as long as all columns combined
    for r in rows:                                          # Loop through each result row
        print("  " + fmt.format(*[str(x) if x is not None else "" for x in r]))  # Print row, replacing None with empty string


def _run_schema_and_procedures(conn):
    """Execute schema.sql and procedures.sql on first run."""
    base = os.path.dirname(os.path.abspath(__file__))   # Get the folder containing this script
    cur  = conn.cursor()                                # Open a DB cursor for executing SQL
    for fname in ("schema.sql", "procedures.sql"):      # Process both SQL files in order
        fpath = os.path.join(base, fname)               # Build full path to the SQL file
        if os.path.exists(fpath):                       # Only run if the file actually exists
            with open(fpath, encoding="utf-8") as f:    # Open the file with UTF-8 encoding
                cur.execute(f.read())                   # Execute the entire SQL file as one statement
    conn.commit()   # Save all schema and procedure changes to the database
    cur.close()     # Release the cursor


# ============================================================
#  Setup — run schema + procedures once
# ============================================================

def setup():
    """Create tables and register all stored procedures/functions."""
    conn = get_connection()             # Open a new DB connection
    _run_schema_and_procedures(conn)    # Run the SQL files to set up tables and procedures
    conn.close()                        # Close the connection after setup
    print("Schema and procedures are ready.")


# ============================================================
#  Practice 7 — kept exactly, updated for new schema
# ============================================================

def insert_from_csv(filepath="contacts.csv"):
    """Extended CSV import: handles email, birthday, group, phone_type."""
    conn = get_connection()     # Open DB connection
    cur  = conn.cursor()        # Open cursor for SQL execution
    inserted = 0                # Counter for successfully inserted contacts
    with open(filepath, newline='', encoding='utf-8') as f:  # Open CSV file
        reader = csv.DictReader(f)      # Parse CSV with header row as keys
        for row in reader:              # Process each row as a dictionary
            # Get or create group
            group_id = None             # Default to no group
            if row.get('group'):        # Only if a group name is present in this row
                cur.execute(
                    "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id;",
                    (row['group'],)     # Insert group or return existing id on name conflict
                )
                group_id = cur.fetchone()[0]     # Store the group's id

            # Insert contact row into contacts table
            cur.execute("""
                INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id;
            """, (row['first_name'], row.get('last_name'), row.get('email'),
                  row.get('birthday') or None, group_id))   # Use None if birthday is blank
            result = cur.fetchone()     # Will be None if the row was skipped due to conflict
            if result:
                contact_id = result[0]  # Get the newly created contact's id
                if row.get('phone'):    # Only insert a phone if one was provided
                    cur.execute("""
                        INSERT INTO phones (contact_id, phone, type)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (contact_id, row['phone'], row.get('phone_type', 'mobile')))  # Default type is mobile
                inserted += 1           # Count this row as successfully inserted
    conn.commit()   # Save all inserts to the database
    cur.close()
    conn.close()
    print(f"Inserted {inserted} contacts from CSV.")


def insert_from_console():
    """Add one contact from console input."""
    print("\n--- Add New Contact ---")
    first_name = input("First name  : ").strip()                        # Read and trim whitespace
    last_name  = input("Last name   : ").strip()
    email      = input("Email       : ").strip()
    birthday   = input("Birthday (YYYY-MM-DD, or blank): ").strip() or None  # None if blank
    phone      = input("Phone       : ").strip()
    phone_type = input("Phone type (home/work/mobile): ").strip() or 'mobile'  # Default to mobile

    # Show available groups so the user knows valid IDs
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, name FROM groups ORDER BY id;")     # Fetch all group names
    groups = cur.fetchall()
    print("Groups: " + ", ".join(f"{g[0]}={g[1]}" for g in groups))    # Print as "1=Friends, 2=Work"
    group_id = input("Group ID (or blank): ").strip() or None   # None if no group selected

    try:
        cur.execute("""
            INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (first_name, last_name or None, email or None, birthday, group_id))  # Blank strings become None
        contact_id = cur.fetchone()[0]      # Get the new contact's id
        if phone:                           # Only insert phone row if a number was entered
            cur.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s);",
                (contact_id, phone, phone_type)
            )
        conn.commit()
        print(f"Contact '{first_name}' added.")
    except Exception as e:
        conn.rollback()     # Undo everything if any step failed
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()


def update_contact():
    """Update first name or a phone number by contact ID."""
    print("\n--- Update Contact ---")
    try:
        cid = int(input("Contact ID to update: ").strip())  # Parse ID as integer
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
            cur.execute("UPDATE contacts SET first_name=%s WHERE id=%s;", (val, cid))  # Update name by contact id
        elif choice == '2':
            old = input("Old phone number: ").strip()   # Must match exactly what's stored
            new = input("New phone number: ").strip()
            cur.execute("UPDATE phones SET phone=%s WHERE contact_id=%s AND phone=%s;", (new, cid, old))  # Match both contact and old number
        else:
            print("Invalid choice.")
            return
        conn.commit()
        print("Updated." if cur.rowcount else "Nothing found to update.")  # rowcount=0 means no rows matched
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
            cur.execute("DELETE FROM contacts WHERE first_name ILIKE %s;", (val,))  # ILIKE = case-insensitive match
        elif choice == '2':
            val = input("Phone: ").strip()
            cur.execute("DELETE FROM phones WHERE phone=%s;", (val,))   # Exact match on phone number
        else:
            print("Invalid choice.")
            return
        conn.commit()
        print(f"Deleted {cur.rowcount} record(s).")     # Report how many rows were actually removed
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
    cur.execute("SELECT id, name FROM groups ORDER BY id;")     # Load all groups to show the menu
    groups = cur.fetchall()
    print("\n--- Filter by Group ---")
    for g in groups:
        print(f"  {g[0]}. {g[1]}")      # Print each group as "  1. Friends"
    try:
        gid = int(input("Group ID: ").strip())  # User picks a group by its numeric id
    except ValueError:
        print("Invalid ID.")
        cur.close(); conn.close(); return

    cur.execute("""
        SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id    -- attach group name via join
        WHERE c.group_id = %s
        ORDER BY c.first_name;
    """, (gid,))
    _print_contacts(cur.fetchall())     # Display results using the shared formatter
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
        WHERE c.email ILIKE %s          -- ILIKE makes the search case-insensitive
        ORDER BY c.first_name;
    """, (f'%{pattern}%',))             # Wrap pattern in % wildcards for substring match
    _print_contacts(cur.fetchall())
    cur.close()
    conn.close()


def sorted_search():
    """Search all contacts and sort by name, birthday, or date added."""
    print("\n--- Sorted Contact List ---")
    print("  Sort by:  1=Name  2=Birthday  3=Date Added")
    choice = input("Choice (1/2/3): ").strip()
    order  = {"1": "c.first_name", "2": "c.birthday", "3": "c.created_at"}.get(choice, "c.first_name")  # Map choice to column; default to name
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER BY {order};               -- Dynamic ORDER BY built from user's choice
    """)
    _print_contacts(cur.fetchall())
    cur.close()
    conn.close()


def paginated_navigation():
    """Navigate contacts page by page."""
    print("\n--- Paginated Navigation ---")
    try:
        limit = int(input("Rows per page: ").strip())   # How many contacts to show per page
    except ValueError:
        print("Invalid number.")
        return

    page = 1        # Start on the first page
    while True:
        offset = (page - 1) * limit     # Calculate how many rows to skip for this page
        conn = get_connection()
        cur  = conn.cursor()

        cur.execute("""
            SELECT
                c.id,
                c.first_name,
                c.last_name,
                c.email,
                c.birthday,
                g.name  AS group_name,
                STRING_AGG(p.phone || ' (' || COALESCE(p.type, '?') || ')', ', ') AS phones  -- Concatenate all phones into one string per contact
            FROM contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            LEFT JOIN phones p ON p.contact_id = c.id
            GROUP BY c.id, c.first_name, c.last_name, c.email, c.birthday, g.name  -- Required when using STRING_AGG
            ORDER BY c.id
            LIMIT %s OFFSET %s;         -- LIMIT caps the rows; OFFSET skips previous pages
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
            print("  (no more results)")  # Reached past the last page

        cmd = input("\n  [next / prev / quit]: ").strip().lower()
        if cmd == 'next':
            if rows:            # Only advance if the current page had results
                page += 1
            else:
                print("  Already at last page.")
        elif cmd == 'prev':
            page = max(1, page - 1)     # max(1,...) prevents going below page 1
        elif cmd == 'quit':
            break


# ============================================================
#  3.3 — Import / Export
# ============================================================

def export_to_json(filepath="contacts_export.json"):
    """Export all contacts with phones and group to a JSON file."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT c.id, c.first_name, c.last_name, c.email,
               c.birthday::TEXT,        -- Cast date to string so JSON serialisation works
               g.name AS group_name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER BY c.id;
    """)
    contacts = cur.fetchall()   # All contact rows

    output = []                 # List that will become the JSON array
    for row in contacts:
        cid = row[0]            # Contact id used to fetch matching phones
        cur.execute("SELECT phone, type FROM phones WHERE contact_id=%s;", (cid,))
        phones = [{"phone": p[0], "type": p[1]} for p in cur.fetchall()]   # Build list of phone dicts
        output.append({         # Build one dict per contact with all fields
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
        json.dump(output, f, indent=2, ensure_ascii=False)  # indent=2 for readable formatting, ensure_ascii=False preserves unicode
    print(f"Exported {len(output)} contacts to '{filepath}'.")


def import_from_json(filepath="contacts_export.json"):
    """Import contacts from JSON. On duplicate name, ask skip or overwrite."""
    if not os.path.exists(filepath):    # Abort early if the file doesn't exist
        print(f"File '{filepath}' not found.")
        return

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)     # Parse the entire JSON file into a Python list

    conn = get_connection()
    cur  = conn.cursor()
    inserted = updated = skipped = 0    # Track outcome counts for the final summary

    for c in data:      # Loop through each contact dict from the JSON
        # Check if a contact with the same first + last name already exists
        cur.execute("""
            SELECT id FROM contacts
            WHERE first_name ILIKE %s AND last_name ILIKE %s;
        """, (c.get('first_name', ''), c.get('last_name', '') or ''))
        existing = cur.fetchone()   # None if no duplicate found

        if existing:
            print(f"  Duplicate: {c['first_name']} {c.get('last_name','')}")
            action = input("  Skip (s) or Overwrite (o)? ").strip().lower()
            if action == 'o':
                group_id = None
                if c.get('group'):      # Re-create or find the group
                    cur.execute(
                        "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id;",
                        (c['group'],)
                    )
                    group_id = cur.fetchone()[0]
                cur.execute("""
                    UPDATE contacts SET email=%s, birthday=%s, group_id=%s
                    WHERE id=%s;
                """, (c.get('email'), c.get('birthday'), group_id, existing[0]))  # Update by the existing contact's id
                cur.execute("DELETE FROM phones WHERE contact_id=%s;", (existing[0],))  # Remove old phones before inserting new ones
                for p in c.get('phones', []):   # Re-insert all phones from JSON
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s);",
                        (existing[0], p['phone'], p.get('type','mobile'))
                    )
                updated += 1
            else:
                skipped += 1    # User chose to skip this duplicate
        else:
            group_id = None
            if c.get('group'):      # Get or create the group for a new contact
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
            cid = cur.fetchone()[0]     # Get the new contact's id for linking phones
            for p in c.get('phones', []):   # Insert each phone entry from the JSON
                cur.execute(
                    "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s);",
                    (cid, p['phone'], p.get('type','mobile'))
                )
            inserted += 1

    conn.commit()   # Save all inserts and updates in one transaction
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
    ptype = input("Type (home/work/mobile): ").strip() or 'mobile'  # Default to mobile if blank
    conn  = get_connection()
    cur   = conn.cursor()
    try:
        cur.execute("CALL add_phone(%s, %s, %s);", (name, phone, ptype))    # Call the stored procedure defined in procedures.sql
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
        cur.execute("CALL move_to_group(%s, %s);", (name, group))   # Procedure handles finding/creating the group internally
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
    cur.execute("SELECT * FROM search_contacts(%s);", (query,))     # Call the SQL function which searches across name, email, and all phone numbers
    rows  = cur.fetchall()
    cur.close()
    conn.close()
    _print_contacts(rows)   # Display results with the shared formatter


# ============================================================
#  Main Menu
# ============================================================

def main():
    setup()     # Run schema.sql and procedures.sql to ensure tables and procedures exist

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

        # Route each menu choice to the matching function
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
            break               # Exit the while loop and end the program
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()      # Only run main() when this file is executed directly, not when imported