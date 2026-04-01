-- functions.sql
CREATE OR REPLACE FUNCTION search_contact_by_name(search_name VARCHAR)
RETURNS TABLE(id INT, first_name VARCHAR, last_name VARCHAR, phone_number VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.first_name, c.last_name, c.phone_number
    FROM contacts c
    WHERE c.first_name ILIKE search_name || '%'; -- ILIKE is case-insensitive
END;
$$ LANGUAGE plpgsql;