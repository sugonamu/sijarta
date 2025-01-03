# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from .utils import authenticate_user, get_db_connection,get_service_categories,get_service_subcategories,get_service_sessions_by_subcategory,get_testimonials_query, get_user_profile
from django.contrib import messages

from django.db import connection
import uuid
from django.utils import timezone

# ==================================== Red ====================================
def mypay_view(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if not user_id:
        return redirect('main:login')

    conn = get_db_connection()
    transactions = []
    balance = 0
    try:
        with conn.cursor() as cursor:
            # Get the user's MyPay balance
            cursor.execute("SELECT MyPayBalance FROM sijarta.users WHERE Id = %s", [user_id])
            row = cursor.fetchone()
            if row:
                balance = row[0]

            # Get the user's transaction history
            cursor.execute("""
                SELECT t.Date, t.Nominal, c.CategoryName 
                FROM sijarta.tr_mypay t
                JOIN sijarta.tr_mypay_category c ON t.CategoryId = c.Id
                WHERE t.UserId = %s
                ORDER BY t.Date DESC
            """, [user_id])
            rows = cursor.fetchall()
            for r in rows:
                transactions.append({
                    'date': r[0],
                    'nominal': r[1],
                    'category': r[2]
                })
    finally:
        conn.close()

    return render(request, 'R_mypay.html', {
        'balance': balance,
        'transactions': transactions,
    })

def mypay_transaction_view(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if not user_id:
        return redirect('main:login')

    service_orders = []
    # If user is a customer, fetch their service orders to pay for
    if user_role == 'customer':
        with connection.cursor() as cursor:
            # Example: Fetch all service orders of this user not yet paid (adjust conditions as needed)
            cursor.execute("""
                SELECT Id, TotalPrice
                FROM sijarta.tr_service_order
                WHERE customerId = %s
                AND Id NOT IN (
                    SELECT serviceTrId 
                    FROM sijarta.tr_order_status 
                    WHERE statusId = (SELECT id FROM sijarta.order_status WHERE status = 'Completed')
                )
            """, [user_id])
            rows = cursor.fetchall()
            for row in rows:
                service_orders.append({'id': row[0], 'totalprice': row[1]})

    if request.method == 'POST':
        category = request.POST.get('category')

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Fetch user current balance
                cursor.execute("SELECT MyPayBalance FROM sijarta.users WHERE Id = %s", [user_id])
                row = cursor.fetchone()
                if row:
                    user_balance = row[0]
                else:
                    user_balance = 0

                if category == 'topup':
                    amount = float(request.POST.get('topup_amount', 0))
                    if amount > 0:
                        # Update user balance
                        cursor.execute("UPDATE sijarta.users SET MyPayBalance = MyPayBalance + %s WHERE Id = %s", [amount, user_id])
                        # Insert transaction record
                        cursor.execute("""
                            INSERT INTO sijarta.tr_mypay (Id, UserId, Date, Nominal, CategoryId)
                            VALUES (gen_random_uuid(), %s, CURRENT_DATE, %s, 
                                    (SELECT Id FROM sijarta.tr_mypay_category WHERE CategoryName = 'topup MyPay'))
                        """, [user_id, amount])
                        messages.success(request, 'Top-up successful!')
                    else:
                        messages.error(request, 'Invalid top-up amount.')

                elif category == 'service_payment' and user_role == 'customer':
                    service_order_id = request.POST.get('service_order_id')
                    # Get the service price
                    cursor.execute("SELECT TotalPrice FROM sijarta.tr_service_order WHERE Id = %s", [service_order_id])
                    price = cursor.fetchone()[0]
                    if price <= user_balance:
                        # Deduct from user's balance
                        cursor.execute("UPDATE sijarta.users SET MyPayBalance = MyPayBalance - %s WHERE Id = %s", [price, user_id])
                        # Insert transaction record
                        cursor.execute("""
                            INSERT INTO sijarta.tr_mypay (Id, UserId, Date, Nominal, CategoryId)
                            VALUES (gen_random_uuid(), %s, CURRENT_DATE, -%s, 
                                    (SELECT Id FROM sijarta.tr_mypay_category WHERE CategoryName = 'pay for service transaction'))
                        """, [user_id, price])
                        messages.success(request, 'Service payment successful!')
                    else:
                        messages.error(request, 'Insufficient balance to pay for service.')

                elif category == 'transfer':
                    recipient_phone = request.POST.get('recipient_phone')
                    transfer_amount = float(request.POST.get('transfer_amount', 0))
                    if transfer_amount > 0 and transfer_amount <= user_balance:
                        # Get recipient ID
                        cursor.execute("SELECT Id FROM sijarta.users WHERE phoneNum = %s", [recipient_phone])
                        recipient = cursor.fetchone()
                        if recipient:
                            recipient_id = recipient[0]
                            # Deduct from user
                            cursor.execute("UPDATE sijarta.users SET MyPayBalance = MyPayBalance - %s WHERE Id = %s", [transfer_amount, user_id])
                            # Add to recipient
                            cursor.execute("UPDATE sijarta.users SET MyPayBalance = MyPayBalance + %s WHERE Id = %s", [transfer_amount, recipient_id])
                            # Insert transaction for sender
                            cursor.execute("""
                                INSERT INTO sijarta.tr_mypay (Id, UserId, Date, Nominal, CategoryId)
                                VALUES (gen_random_uuid(), %s, CURRENT_DATE, -%s, 
                                        (SELECT Id FROM sijarta.tr_mypay_category WHERE CategoryName = 'transfer MyPay to another user'))
                            """, [user_id, transfer_amount])
                            # Insert transaction for receiver
                            cursor.execute("""
                                INSERT INTO sijarta.tr_mypay (Id, UserId, Date, Nominal, CategoryId)
                                VALUES (gen_random_uuid(), %s, CURRENT_DATE, %s, 
                                        (SELECT Id FROM sijarta.tr_mypay_category WHERE CategoryName = 'receive service transaction honorarium'))
                            """, [recipient_id, transfer_amount])
                            messages.success(request, 'Transfer successful!')
                        else:
                            messages.error(request, 'Recipient not found.')
                    else:
                        messages.error(request, 'Invalid or insufficient amount for transfer.')

                elif category == 'withdrawal':
                    bank_name = request.POST.get('bank_name')
                    bank_account_number = request.POST.get('bank_account_number')
                    withdrawal_amount = float(request.POST.get('withdrawal_amount', 0))
                    if withdrawal_amount > 0 and withdrawal_amount <= user_balance:
                        # Deduct from user
                        cursor.execute("UPDATE sijarta.users SET MyPayBalance = MyPayBalance - %s WHERE Id = %s", [withdrawal_amount, user_id])
                        # Insert transaction record
                        cursor.execute("""
                            INSERT INTO sijarta.tr_mypay (Id, UserId, Date, Nominal, CategoryId)
                            VALUES (gen_random_uuid(), %s, CURRENT_DATE, -%s, 
                                    (SELECT Id FROM sijarta.tr_mypay_category WHERE CategoryName = 'withdrawal MyPay to bank account'))
                        """, [user_id, withdrawal_amount])
                        messages.success(request, 'Withdrawal successful!')
                    else:
                        messages.error(request, 'Invalid or insufficient amount for withdrawal.')

                conn.commit()
                return redirect('main:mypay')
        except Exception as e:
            conn.rollback()
            messages.error(request, f'Error processing transaction: {str(e)}')
        finally:
            conn.close()

    return render(request, 'R_mypay_transaction.html', {
        'user_role': user_role,
        'service_orders': service_orders,
    })

def managejob(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if not user_id or user_role != 'worker':
        return redirect('main:login')

    conn = get_db_connection()
    available_orders = []
    categories = []
    subcategories = []
    selected_category = request.GET.get('category', '')
    selected_subcategory = request.GET.get('subcategory', '')
    try:
        with conn.cursor() as cursor:
            # Fetch all service categories
            cursor.execute("SELECT id, categoryname FROM sijarta.service_category")
            categories = cursor.fetchall()

            # Fetch subcategories if a category is selected
            if selected_category:
                cursor.execute("""
                    SELECT id, subcategoryname
                    FROM sijarta.service_subcategory
                    WHERE servicecategoryid = %s
                """, [selected_category])
                subcategories = cursor.fetchall()

            # Fetch all available service orders with status "Looking for Nearby Worker"
            query = """
                SELECT so.Id, so.orderDate, so.serviceDate, so.serviceTime, so.TotalPrice,
                       sc.subcategoryname, sc.description,
                       u.name as customer_name, sc.id as subcategory_id,
                       so.session
                FROM sijarta.tr_service_order so
                JOIN sijarta.service_subcategory sc ON so.SubcategoryId = sc.id
                JOIN sijarta.tr_order_status tos ON so.Id = tos.serviceTrId
                JOIN sijarta.order_status os ON tos.statusId = os.id
                JOIN sijarta.users u ON so.customerId = u.id
                WHERE os.status = 'Finding Nearest Worker'
            """
            params = []
            if selected_subcategory:
                query += " AND sc.id = %s"
                params.append(selected_subcategory)
            elif selected_category:
                query += " AND sc.servicecategoryid = %s"
                params.append(selected_category)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                available_orders.append({
                    'id': row[0],
                    'order_date': row[1],
                    'service_date': row[2],
                    'service_time': row[3],
                    'total_price': row[4],
                    'subcategory_name': row[5],
                    'description': row[6],
                    'customer_name': row[7],
                    'subcategory_id': row[8],
                    'session': row[9],
                })
    finally:
        conn.close()

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Update the order status to "Worker Assigned"
                cursor.execute("""
                    UPDATE sijarta.tr_order_status
                    SET statusId = (SELECT id FROM sijarta.order_status WHERE status = 'Worker Assigned'),
                        date = CURRENT_TIMESTAMP
                    WHERE serviceTrId = %s
                """, [order_id])
                
                # Update the service order with the worker ID and job date
                cursor.execute("""
                    UPDATE sijarta.tr_service_order
                    SET workerId = %s,
                        serviceDate = CURRENT_DATE,
                        serviceTime = CURRENT_TIMESTAMP
                    WHERE Id = %s
                """, [user_id, order_id])
                
                # Calculate job duration (assuming 1 session = 1 day)
                cursor.execute("""
                    SELECT session FROM sijarta.tr_service_order WHERE Id = %s
                """, [order_id])
                session_row = cursor.fetchone()
                if session_row:
                    session = session_row[0]
                    # Update the service order with the job duration
                    cursor.execute("""
                        UPDATE sijarta.tr_service_order
                        SET serviceDate = CURRENT_DATE + INTERVAL '%s day'
                        WHERE Id = %s
                    """, [session, order_id])
                
                conn.commit()
                messages.success(request, 'Order accepted successfully!')
                return redirect('main:managejob')
        except Exception as e:
            if conn:
                conn.rollback()
            messages.error(request, f'Error accepting order: {str(e)}')
        finally:
            conn.close()

    return render(request, 'R_manage_job.html', {
        'available_orders': available_orders,
        'categories': categories,
        'subcategories': subcategories,
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
    })

def manage_order_status(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if not user_id or user_role != 'worker':
        return redirect('main:login')

    conn = get_db_connection()
    active_orders = []
    search_name = request.GET.get('service_name', '')
    search_status = request.GET.get('service_status', '')
    try:
        with conn.cursor() as cursor:
            # Fetch all active service orders for the current worker
            query = """
                SELECT so.Id, so.orderDate, so.serviceDate, so.serviceTime, so.TotalPrice,
                       sc.subcategoryname, os.status,
                       u.name as customer_name, so.session
                FROM sijarta.tr_service_order so
                JOIN sijarta.service_subcategory sc ON so.SubcategoryId = sc.id
                JOIN sijarta.tr_order_status tos ON so.Id = tos.serviceTrId
                JOIN sijarta.order_status os ON tos.statusId = os.id
                JOIN sijarta.users u ON so.customerId = u.id
                WHERE so.workerId = %s
            """
            params = [user_id]
            if search_name:
                query += " AND sc.subcategoryname ILIKE %s"
                params.append(f"%{search_name}%")
            if search_status:
                query += " AND os.status = %s"
                params.append(search_status)
            query += " ORDER BY so.serviceDate DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                active_orders.append({
                    'id': row[0],
                    'order_date': row[1],
                    'service_date': row[2],
                    'service_time': row[3],
                    'total_price': row[4],
                    'subcategory_name': row[5],
                    'status': row[6],
                    'customer_name': row[7],
                    'session': row[8],
                })
    finally:
        conn.close()

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('new_status')
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Update the order status
                cursor.execute("""
                    UPDATE sijarta.tr_order_status
                    SET statusId = (SELECT id FROM sijarta.order_status WHERE status = %s),
                        date = CURRENT_TIMESTAMP
                    WHERE serviceTrId = %s
                """, [new_status, order_id])
                conn.commit()
                messages.success(request, f'Order status updated to {new_status}!')
                return redirect('main:manage_order_status')
        except Exception as e:
            if conn:
                conn.rollback()
            messages.error(request, f'Error updating order status: {str(e)}')
        finally:
            conn.close()

    return render(request, 'R_manage_order_status.html', {
        'active_orders': active_orders,
        'search_name': search_name,
        'search_status': search_status,
    })



# ==================================== Yellow ====================================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate_user(username, password)
        if user:
            # Convert UUID to string before storing it in the session
            request.session['user_id'] = str(user[0])
            request.session['user_role'] = user[1]
            request.session['username'] = username
            return redirect('main:success')  # Include the namespace
        else:
            return render(request, 'Y_login.html', {'error': 'Invalid credentials'})
    return render(request, 'Y_login.html')

def register_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        phone = request.POST['phone']
        password = request.POST['password']  # Store password as plaintext
        sex = request.POST['sex']
        dob = request.POST.get('dob', None)
        address = request.POST.get('address', None)
        role = request.POST['role']
        
        # Worker-specific fields (only included if role is 'worker')
        bank_name = request.POST.get('bank_name', '')
        account_number = request.POST.get('account_number', '')
        npwp = request.POST.get('npwp', '')
        image_url = request.POST.get('image_url', '')

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Insert user into the database
                cursor.execute("""
                    INSERT INTO sijarta.users (id, name, sex, phoneNum, pwd, dob, address, myPayBalance)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, 0)
                """, (name, sex, phone, password, dob, address))
                
                # Insert into customer or worker table based on role
                if role == 'customer':
                    cursor.execute("""
                        INSERT INTO sijarta.customer (id, level)
                        VALUES ((SELECT id FROM sijarta.users WHERE phoneNum = %s), 'Basic')
                    """, [phone])
                elif role == 'worker':
                    # Insert into the worker table with the additional fields
                    cursor.execute("""
                        INSERT INTO sijarta.worker (id, bankName, accNumber, npwp, picUrl, rate, totalFinishOrder)
                        VALUES ((SELECT id FROM sijarta.users WHERE phoneNum = %s), %s, %s, %s, %s, 0, 0)
                    """, [phone, bank_name, account_number, npwp, image_url])

            conn.commit()
            messages.success(request, 'Registration successful!')
            return redirect('main:login')
        except Exception as e:
            conn.rollback()
            messages.error(request, f'Error during registration: {str(e)}')
        finally:
            conn.close()

    return render(request, 'Y_register.html')

def logout(request):
    auth_logout(request) 
    return redirect('main:login')  

def profile(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if not user_id:
        return redirect('main:login')

    conn = get_db_connection()
    user_profile = None
    try:
        with conn.cursor() as cursor:
            # Fetch user profile data
            cursor.execute("""
                SELECT u.Id, u.Name, u.PhoneNum, u.Sex, u.DoB, u.Address, u.MyPayBalance,
                       CASE WHEN EXISTS(SELECT 1 FROM sijarta.customer c WHERE c.Id = u.Id) THEN 'customer'
                            WHEN EXISTS(SELECT 1 FROM sijarta.worker w WHERE w.Id = u.Id) THEN 'worker'
                            ELSE NULL END as role,
                        w.BankName, w.Accnumber, w.NPWP, w.PicURL
                FROM sijarta.users u
                LEFT JOIN sijarta.worker w ON u.Id = w.Id
                WHERE u.Id = %s
                LIMIT 1;
            """, [user_id])
            row = cursor.fetchone()
            if row:
                user_profile = {
                    'id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'sex': row[3],
                    'dob': row[4],
                    'address': row[5],
                    'mypay_balance': row[6],
                    'role': row[7],
                    'bank_name': row[8],
                    'acc_number': row[9],
                    'npwp': row[10],
                    'pic_url': row[11],
                }
    finally:
        conn.close()

    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        phone = request.POST.get('phone')
        birth_date = request.POST.get('birth_date')
        address = request.POST.get('address')
        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')
        npwp = request.POST.get('npwp')
        image = request.POST.get('image')
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Update user data if changed
                update_fields = []
                params = []
                if name and name != user_profile['name']:
                    update_fields.append("Name = %s")
                    params.append(name)
                if password:
                    update_fields.append("Pwd = %s")
                    params.append(password)
                if sex and sex != user_profile['sex']:
                    update_fields.append("Sex = %s")
                    params.append(sex)
                if phone and phone != user_profile['phone']:
                    update_fields.append("PhoneNum = %s")
                    params.append(phone)
                if birth_date and birth_date != str(user_profile['dob']):
                    update_fields.append("DoB = %s")
                    params.append(birth_date)
                if address and address != user_profile['address']:
                    update_fields.append("Address = %s")
                    params.append(address)
                
                if update_fields:
                    query = f"UPDATE sijarta.users SET {', '.join(update_fields)} WHERE Id = %s"
                    params.append(user_id)
                    cursor.execute(query, params)

                if user_role == 'worker':
                    worker_update_fields = []
                    worker_params = []
                    if bank_name and bank_name != user_profile['bank_name']:
                        worker_update_fields.append("BankName = %s")
                        worker_params.append(bank_name)
                    if account_number and account_number != user_profile['acc_number']:
                        worker_update_fields.append("Accnumber = %s")
                        worker_params.append(account_number)
                    if npwp and npwp != user_profile['npwp']:
                        worker_update_fields.append("NPWP = %s")
                        worker_params.append(npwp)
                    if image and image != user_profile['pic_url']:
                        worker_update_fields.append("PicURL = %s")
                        worker_params.append(image)
                    
                    if worker_update_fields:
                        query = f"UPDATE sijarta.worker SET {', '.join(worker_update_fields)} WHERE Id = %s"
                        worker_params.append(user_id)
                        cursor.execute(query, worker_params)
                
                conn.commit()
                messages.success(request, 'Profile updated successfully!')
                return redirect('main:profile')
        except Exception as e:
            if conn:
                conn.rollback()
            messages.error(request, f'Error updating profile: {str(e)}')
        finally:
            conn.close()

    return render(request, 'Y_profile.html', {
        'profile': user_profile,
    })


# ==================================== Green ====================================

def success_view(request):
    # Retrieve session data
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    username = request.session.get('username', 'Guest')

    # Get service categories from the database
    categories = get_service_categories()

    # Prepare the context with categories and subcategories
    categories_with_subcategories = []
    for category in categories:
        subcategories = get_service_subcategories(category[0])  # Assuming category[0] is the category ID
        categories_with_subcategories.append({
            'category': category,
            'subcategories': subcategories,
        })

    # Render the success page with categories and their subcategories
    return render(request, 'success.html', {
        'user_id': user_id,
        'user_role': user_role,
        'username': username,
        'categories_with_subcategories': categories_with_subcategories,  # Use the new structure
    })

def subcategory_user(request, subcategory_name):
    from django.db import connection

    # Call the utility function to get the grouped sessions for the specific subcategory
    grouped_sessions = get_service_sessions_by_subcategory(subcategory_name)

    # Fetch testimonials
    testimonials = []
    with connection.cursor() as cursor:
        cursor.execute(get_testimonials_query(subcategory_name), [subcategory_name])
        rows = cursor.fetchall()
        for row in rows:
            testimonials.append({
                'customer_name': row[0],
                'review': row[1],
                'rating': row[2],
                'service_date': row[3],
                'worker_name': row[4],
            })

    # Pass the data to the template
    return render(request, 'subcategory_user.html', {
        'subcategory_name': subcategory_name,
        'grouped_sessions': grouped_sessions,
        'testimonials': testimonials,
    })

def subcategory_worker(request, subcategory_name):

    # Call the utility function to get the grouped sessions for the specific subcategory
    grouped_sessions = get_service_sessions_by_subcategory(subcategory_name)

    # Fetch testimonials
    testimonials = []
    with connection.cursor() as cursor:
        cursor.execute(get_testimonials_query(subcategory_name), [subcategory_name])
        rows = cursor.fetchall()
        for row in rows:
            testimonials.append({
                'customer_name': row[0],
                'review': row[1],
                'rating': row[2],
                'service_date': row[3],
                'worker_name': row[4],
            })

    # Pass the data to the template
    return render(request, 'subcategory_worker.html', {
        'subcategory_name': subcategory_name,
        'grouped_sessions': grouped_sessions,
        'testimonials': testimonials,
    })

def myorder(request):
    return render(request, 'myorder.html')

# ==================================== Blue ====================================
def discount(request):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Assume the user's ID is retrieved from the session
    user_id = request.session.get("user_id")

    # Fetch user balance
    cursor.execute("SELECT MyPayBalance FROM sijarta.USERS WHERE Id = %s", (user_id,))
    user_balance_row = cursor.fetchone()
    if user_balance_row:
        mypay_balance = user_balance_row[0]
    else:
        mypay_balance = 0  # Default to 0 if user not found

    # Fetch vouchers
    cursor.execute("SELECT Code, NmbDayValid, UserQuota, Price FROM sijarta.voucher")
    vouchers = [
        {"Code": row[0], "NmbDayValid": row[1], "UserQuota": row[2], "Price": row[3]}
        for row in cursor.fetchall()
    ]

    # Fetch promos
    cursor.execute("SELECT Code, OfferEndDate FROM sijarta.promo")
    promos = [
        {"Code": row[0], "OfferEndDate": row[1]}
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return render(request, 'discounts.html', {
        "vouchers": vouchers,
        "promos": promos,
        "user": {"mypay_balance": mypay_balance}
    })

def buy_voucher(request, voucher_code):
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()

        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "User not logged in"}, status=403)

        cursor.execute("SELECT Price FROM sijarta.voucher WHERE Code = %s", (voucher_code,))
        voucher_row = cursor.fetchone()
        if not voucher_row:
            conn.close()
            return JsonResponse({"error": "Voucher not found"}, status=404)

        voucher_price = voucher_row[0]
        cursor.execute("SELECT MyPayBalance FROM sijarta.USERS WHERE Id = %s", (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return JsonResponse({"error": "User not found"}, status=404)

        user_balance = user_row[0]
        if user_balance >= voucher_price:
            new_balance = user_balance - voucher_price
            cursor.execute("UPDATE sijarta.USERS SET MyPayBalance = %s WHERE Id = %s", (new_balance, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return JsonResponse({"success": True, "new_balance": new_balance})
        else:
            conn.close()
            return JsonResponse({"error": "Insufficient balance"}, status=400)

def buy_promo(request, promo_code):
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()

        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"error": "User not logged in"}, status=403)

        cursor.execute("SELECT Discount FROM sijarta.promo WHERE Code = %s", (promo_code,))
        promo_row = cursor.fetchone()
        if not promo_row:
            conn.close()
            return JsonResponse({"error": "Promo not found"}, status=404)

        promo_price = 5  # Example price for all promos
        cursor.execute("SELECT MyPayBalance FROM sijarta.USERS WHERE Id = %s", (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return JsonResponse({"error": "User not found"}, status=404)

        user_balance = user_row[0]
        if user_balance >= promo_price:
            new_balance = user_balance - promo_price
            cursor.execute("UPDATE sijarta.USERS SET MyPayBalance = %s WHERE Id = %s", (new_balance, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return JsonResponse({"success": True, "new_balance": new_balance})
        else:
            conn.close()
            return JsonResponse({"error": "Insufficient balance"}, status=400)



