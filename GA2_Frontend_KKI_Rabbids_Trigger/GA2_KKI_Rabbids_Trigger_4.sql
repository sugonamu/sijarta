CREATE OR REPLACE FUNCTION transfer_payment_to_worker()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if the status of the service order is "Completed"
    IF NEW.statusId = (SELECT id FROM sijarta.order_status WHERE status = 'Completed') THEN
        -- Update the worker's MyPay balance
        UPDATE sijarta.users
        SET MyPayBalance = COALESCE(MyPayBalance, 0) +
            (SELECT TotalPrice 
             FROM sijarta.tr_service_order 
             WHERE Id = NEW.serviceTrId)
        WHERE Id = (SELECT workerId 
                    FROM sijarta.tr_service_order 
                    WHERE Id = NEW.serviceTrId);

        -- Deduct the service price from the customer's MyPay balance
        UPDATE sijarta.users
        SET MyPayBalance = COALESCE(MyPayBalance, 0) -
            (SELECT TotalPrice 
             FROM sijarta.tr_service_order 
             WHERE Id = NEW.serviceTrId)
        WHERE Id = (SELECT customerId 
                    FROM sijarta.tr_service_order 
                    WHERE Id = NEW.serviceTrId);

        -- Insert a record into the TR_MYPAY table to categorize the transaction for the worker
        INSERT INTO sijarta.tr_mypay (Id, UserId, Date, Nominal, CategoryId)
        VALUES (
            gen_random_uuid(),
            (SELECT workerId FROM sijarta.tr_service_order WHERE Id = NEW.serviceTrId),
            CURRENT_DATE,
            (SELECT TotalPrice FROM sijarta.tr_service_order WHERE Id = NEW.serviceTrId),
            (SELECT Id FROM sijarta.tr_mypay_category WHERE CategoryName = 'receive service transaction honorarium')
        );

        -- Insert a record into the TR_MYPAY table to categorize the transaction for the customer
        INSERT INTO sijarta.tr_mypay (Id, UserId, Date, Nominal, CategoryId)
        VALUES (
            gen_random_uuid(),
            (SELECT customerId FROM sijarta.tr_service_order WHERE Id = NEW.serviceTrId),
            CURRENT_DATE,
            -(SELECT TotalPrice FROM sijarta.tr_service_order WHERE Id = NEW.serviceTrId),
            (SELECT Id FROM sijarta.tr_mypay_category WHERE CategoryName = 'pay for service transaction')
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER after_order_status_update
AFTER UPDATE OF statusId ON sijarta.tr_order_status
FOR EACH ROW
EXECUTE FUNCTION transfer_payment_to_worker();