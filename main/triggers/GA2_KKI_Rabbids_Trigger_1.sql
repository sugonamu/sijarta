-- Registered Phone No Check --
-- Function --
CREATE OR REPLACE FUNCTION check_phone_number_unique()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sijarta.USERS
        WHERE PhoneNum = NEW.PhoneNum
          AND Id <> NEW.Id
    ) THEN
        RAISE EXCEPTION 'Phone number % is already registered', NEW.PhoneNum;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- Trigger --
CREATE TRIGGER before_user_insert_or_update
BEFORE INSERT OR UPDATE ON sijarta.USERS
FOR EACH ROW
EXECUTE FUNCTION check_phone_number_unique();


-- Bank Name & Account Number Pair Check (Worker) --
-- Function --
CREATE OR REPLACE FUNCTION check_bank_account_pair_unique()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sijarta.WORKER
        WHERE BankName = NEW.BankName
          AND Accnumber = NEW.Accnumber
          AND Id <> NEW.Id  
    ) THEN
        RAISE EXCEPTION 'Bank Name % and Account Number % pair is already registered', NEW.BankName, NEW.Accnumber;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger --
CREATE TRIGGER before_worker_insert_or_update
BEFORE INSERT OR UPDATE ON sijarta.WORKER
FOR EACH ROW
EXECUTE FUNCTION check_bank_account_pair_unique();
