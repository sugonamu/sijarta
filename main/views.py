# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from .utils import authenticate_user, get_db_connection,get_service_categories,get_service_subcategories,get_service_sessions_by_subcategory,get_testimonials_query
from django.contrib import messages

from django.db import connection
import uuid
from django.utils import timezone


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
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


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
                if role == 'user':
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

    return render(request, 'register.html')

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

    return render(request, 'mypay.html', {
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

    return render(request, 'mypay_transaction.html', {
        'user_role': user_role,
        'service_orders': service_orders,
    })

def logout(request):
    auth_logout(request) 
    return redirect('main:login')  

def profile(request):
    return render(request, 'profile.html')

def manage_order_status(request):
    return render(request, 'manage_order_status.html')

def managejob(request):
    return render(request, 'manage_job.html')

def myorder(request):
    return render(request, 'myorder.html')

def discount(request):
    return render(request, 'discounts.html')
