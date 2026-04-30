-- ============================================================
--  procedures.sql  —  New PL/pgSQL stored objects for TSIS1
--  Run after schema.sql:
--      psql -U <user> -d phonebook -f procedures.sql
--
--  Procedures already in Practice 8 (NOT duplicated here):
--    upsert_contact, insert_many_contacts,
--    delete_by_username_or_phone, search_by_pattern, get_page
-- ============================================================


-- ============================================================
--  Procedure: add_phone
--  Adds a new phone number to an existing contact by name.
--  p_type must be 'home', 'work', or 'mobile'.
-- ============================================================
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- Find contact by first_name (case-insensitive)
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE first_name ILIKE p_contact_name
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);
END;
$$;


-- ============================================================
--  Procedure: move_to_group
--  Moves a contact to a different group.
--  Creates the group if it does not already exist.
-- ============================================================
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id   INTEGER;
    v_contact_id INTEGER;
BEGIN
    -- Get or create the group
    SELECT id INTO v_group_id FROM groups WHERE name ILIKE p_group_name;

    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name)
        RETURNING id INTO v_group_id;
    END IF;

    -- Find contact
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE first_name ILIKE p_contact_name
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;
END;
$$;


-- ============================================================
--  Function: search_contacts
--  Extends Practice 8 search to also match email and all phones
--  in the phones table (since phones are now in a separate table).
-- ============================================================
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id         INT,
    first_name VARCHAR,
    last_name  VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.first_name,
        c.last_name,
        c.email,
        c.birthday,
        g.name AS group_name
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE c.first_name ILIKE '%' || p_query || '%'
       OR c.last_name  ILIKE '%' || p_query || '%'
       OR c.email      ILIKE '%' || p_query || '%'
       OR p.phone      ILIKE '%' || p_query || '%'
    ORDER BY c.first_name;
END;
$$;
