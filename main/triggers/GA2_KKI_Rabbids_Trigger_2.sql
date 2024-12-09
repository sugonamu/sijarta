CREATE OR REPLACE FUNCTION sijarta.refund_mypay_on_order_cancel(serviceTrId UUID) 
RETURNS VOID AS $$
DECLARE
    v_customerId UUID;
    v_paymentAmount DECIMAL(10, 2);
BEGIN
    -- getting customer ID
    SELECT customerId INTO v_customerId
    FROM sijarta.tr_service_order
    WHERE Id = serviceTrId;

    -- getting payment amount
    SELECT Nominal INTO v_paymentAmount
    FROM sijarta.tr_mypay
    WHERE UserId = v_customerId
    AND Id = (SELECT MAX(Id) FROM sijarta.tr_mypay WHERE UserId = v_customerId);

    --refund payment amount
    UPDATE sijarta.USERS
    SET MyPayBalance = MyPayBalance + v_paymentAmount
    WHERE Id = v_customerId;

   
    INSERT INTO sijarta.tr_mypay(UserId, Date, Nominal, CategoryId)
    VALUES (v_customerId, CURRENT_DATE, v_paymentAmount, 'MY01'); -- Assume MY01 is topup MyPay
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sijarta.trigger_refund_on_order_cancel()
RETURNS TRIGGER AS $$
BEGIN
    -- check if status is cancel
    IF NEW.status = 'Cancelled' THEN
       
        PERFORM sijarta.refund_mypay_on_order_cancel(NEW.serviceTrId);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_order_cancel
AFTER INSERT ON sijarta.tr_order_status
FOR EACH ROW
EXECUTE FUNCTION sijarta.trigger_refund_on_order_cancel();
