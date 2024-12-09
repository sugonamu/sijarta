# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from .utils import authenticate_user, get_db_connection,get_service_categories,get_service_subcategories
from django.contrib import messages

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
                    cursor.execute("""
                        INSERT INTO sijarta.worker (id, bankName, accNumber, npwp, picUrl, rate, totalFinishOrder)
                        VALUES ((SELECT id FROM sijarta.users WHERE phoneNum = %s), '', '', '', '', 0, 0)
                    """, [phone])
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

def subcategory_detail(request, subcategory_name):
    # For now, we pass the subcategory_name directly as context
    return render(request, 'subcategory_user.html', {
        'subcategory_name': subcategory_name
    })