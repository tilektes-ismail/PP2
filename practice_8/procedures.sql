-- procedures.sql
CREATE OR REPLACE PROCEDURE add_new_contact(
    p_first VARCHAR, 
    p_last VARCHAR, 
    p_phone VARCHAR
)
AS $$
BEGIN
    INSERT INTO contacts (first_name, last_name, phone_number)
    VALUES (p_first, p_last, p_phone);
    COMMIT; -- Procedures can handle their own transactions
END;
$$ LANGUAGE plpgsql;