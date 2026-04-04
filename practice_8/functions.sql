-- ============================================================
-- Practice 8: PhoneBook Functions
-- ============================================================

-- 1. Function that returns all records matching a pattern
--    (searches by part of first_name, username, or phone)
-- ============================================================
CREATE OR REPLACE FUNCTION search_contacts(pattern TEXT)
RETURNS TABLE(id INT, first_name VARCHAR, username VARCHAR, phone VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
        SELECT c.id, c.first_name, c.username, c.phone
        FROM contacts c
        WHERE c.first_name ILIKE '%' || pattern || '%'
           OR c.username   ILIKE '%' || pattern || '%'
           OR c.phone      ILIKE '%' || pattern || '%';
END;
$$;


-- 4. Function that queries contacts with pagination (LIMIT + OFFSET)
-- ============================================================
CREATE OR REPLACE FUNCTION get_contacts_paginated(page_limit INT, page_offset INT)
RETURNS TABLE(id INT, first_name VARCHAR, username VARCHAR, phone VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
        SELECT c.id, c.first_name, c.username, c.phone
        FROM contacts c
        ORDER BY c.id
        LIMIT page_limit OFFSET page_offset;
END;
$$;


-- ============================================================
-- Usage examples:
--   SELECT * FROM search_contacts('Bek');
--   SELECT * FROM search_contacts('+770');
--   SELECT * FROM get_contacts_paginated(10, 0);   -- page 1
--   SELECT * FROM get_contacts_paginated(10, 10);  -- page 2
-- ============================================================
