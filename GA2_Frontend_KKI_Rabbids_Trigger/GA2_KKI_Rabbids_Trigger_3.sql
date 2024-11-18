CREATE TRIGGER CheckVoucherValidity
BEFORE INSERT ON Transactions
FOR EACH ROW
BEGIN
   DECLARE VUsage INT;
   DECLARE VExp DATE;

   SELECT UsageCount, ExpirationDate 
   INTO VUsage, VExp
   FROM Vouchers
   WHERE VCode = NEW.VCode;

   IF VUsage >= LUsage THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Voucher usage limit exceeded.';
   END IF;

   IF VExp < CURRENT_DATE THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Voucher expired.';
   END IF;

   UPDATE Vouchers
   SET UsageCount = UsageCount + 1
   WHERE VCode = NEW.VCode;
END;
