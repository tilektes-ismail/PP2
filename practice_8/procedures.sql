
-- 2. Procedure: insert a new user by name and phone.
--    If the username already exists → update their phone.
-- ============================================================
CREATE OR REPLACE PROCEDURE upsert_contact(
    p_first_name VARCHAR,
    p_username   VARCHAR,
    p_phone      VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM contacts WHERE username = p_username) THEN
        UPDATE contacts
        SET first_name = p_first_name,
            phone      = p_phone
        WHERE username = p_username;
        RAISE NOTICE 'Updated existing contact: %', p_username;
    ELSE
        INSERT INTO contacts (first_name, username, phone)
        VALUES (p_first_name, p_username, p_phone);
        RAISE NOTICE 'Inserted new contact: %', p_username;
    END IF;
END;
$$;


-- 3. Procedure: insert many users from arrays of names, usernames and phones.
--    Uses a loop + IF to validate phone format.
--    Collects and returns all rows with invalid phone numbers.
-- ============================================================
CREATE OR REPLACE PROCEDURE insert_many_contacts(
    p_first_names VARCHAR[],
    p_usernames   VARCHAR[],
    p_phones      VARCHAR[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    i           INT;
    total       INT;
    bad_records TEXT := '';
BEGIN
    total := array_length(p_first_names, 1);

    FOR i IN 1..total LOOP
        -- Validate: phone must contain digits only (spaces and dashes are allowed and stripped)
        -- Strip spaces and dashes before validating, then store the cleaned version
        IF regexp_replace(p_phones[i], '[\s\-]', '', 'g') ~ '^[0-9]+$' THEN
            INSERT INTO contacts (first_name, username, phone)
            VALUES (p_first_names[i], p_usernames[i], regexp_replace(p_phones[i], '[\s\-]', '', 'g'))
            ON CONFLICT (username) DO UPDATE
                SET first_name = EXCLUDED.first_name,
                    phone      = EXCLUDED.phone;
        ELSE
            bad_records := bad_records ||
                format('Row %s → name: %s, username: %s, phone: %s | ',
                       i, p_first_names[i], p_usernames[i], p_phones[i]);
        END IF;
    END LOOP;

    IF bad_records <> '' THEN
        RAISE NOTICE 'Invalid records (skipped): %', bad_records;
    ELSE
        RAISE NOTICE 'All records inserted successfully.';
    END IF;
END;
$$;


-- 5. Procedure: delete a contact by username OR by phone number.
-- ============================================================
CREATE OR REPLACE PROCEDURE delete_contact(
    p_username VARCHAR DEFAULT NULL,
    p_phone    VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    rows_deleted INT;
BEGIN
    IF p_username IS NOT NULL THEN
        DELETE FROM contacts WHERE username = p_username;
        GET DIAGNOSTICS rows_deleted = ROW_COUNT;
        RAISE NOTICE 'Deleted % row(s) by username: %', rows_deleted, p_username;

    ELSIF p_phone IS NOT NULL THEN
        DELETE FROM contacts WHERE phone = p_phone;
        GET DIAGNOSTICS rows_deleted = ROW_COUNT;
        RAISE NOTICE 'Deleted % row(s) by phone: %', rows_deleted, p_phone;

    ELSE
        RAISE EXCEPTION 'Provide at least one of: p_username or p_phone';
    END IF;
END;
$$;


