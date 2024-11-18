from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import LoginForm
from .models import UserProfile,ServiceCategory,SubCategory,Testimonial, MyPayTransaction, ServiceOrder, ServiceSession, Promo, Voucher
import datetime
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from decimal import Decimal
from django.utils.timezone import now
from datetime import date


def home(request):
    user_profile = None
    user_role = None

    # Check if the user is authenticated before querying the UserProfile model
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            user_role = user_profile.role
        except UserProfile.DoesNotExist:
            pass  # Handle cases where the UserProfile does not exist

    # Fetch categories with their subcategories
    categories = ServiceCategory.objects.prefetch_related('subcategories').all()

    # Get selected category and search term from request
    selected_category = request.GET.get('category', '')
    search_term = request.GET.get('search', '')

    # Filter categories if a specific category is selected
    if selected_category:
        categories = categories.filter(id=selected_category)

    # Apply search filter if a search term is entered
    if search_term:
        categories = categories.filter(
            Q(name__icontains=search_term) |
            Q(subcategories__name__icontains=search_term)
        ).distinct()

    # Prepare the context for rendering
    context = {
        'categories': categories,
        'search_term': search_term,
        'user_profile': user_profile,
    }
    return render(request, 'success.html', context)

def user_booking_page(request):
    # Example hardcoded data, replace with actual database queries later
    bookings = [
        {
            'subcategory': 'Subcategory 1',
            'service_session': 'Service Session 3',
            'total_payment': 'Rp 1,000,000',
            'worker': 'jontheworker',
            'status': 'Waiting for payment',
        },
        {
            'subcategory': 'Subcategory 2',
            'service_session': 'Service Session 2',
            'total_payment': 'Rp 2,000,000',
            'worker': 'robtheworker',
            'status': 'Order Completed',
        },
        {
            'subcategory': 'Subcategory 3',
            'service_session': 'Service Session 1',
            'total_payment': 'Rp 1,000,000',
            'worker': 'None',
            'status': 'Searching for Nearest Workers',
        },
    ]

    return render(request, 'userbookingpage.html', {'bookings': bookings})
def booking_service(request):
    context = {
        'current_date': date.today().strftime('%d %B %Y'),  # Formats date as "Day Month Year"
    }
    return render(request, 'booking_services.html', context)

@login_required
def worker_profile(request):
    # Example: Replace these fields with actual database queries for the logged-in worker
    worker = {
        'name': UserProfile.objects.get(user=request.user),
        'rate': '7/10',
        'finished_order_count': 3,
        'phone_number': '081281412990',
        'birth_date': '7 November 1980',
        'address': 'Grove Street',
    }
    return render(request, 'worker_profile.html', {'worker': worker})
@login_required(login_url='/login/')
def subcategory_detail(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    user_profile = UserProfile.objects.get(user=request.user)

    # Fetch workers, testimonials, and sessions for rendering in the template
    workers = subcategory.workers.all()
    testimonials = subcategory.testimonials.all()
    sessions = subcategory.sessions.all()

    # Handle "Join Service Category" action for workers
    if request.method == 'POST' and user_profile.role == 'worker':
        # Check if the worker is already in the list
        if user_profile not in subcategory.workers.all():
            subcategory.workers.add(user_profile)  # Add the worker to the service category
            subcategory.save()

        # Redirect to the same page to update the list of workers
        if user_profile.role=="worker":
            return redirect('subcategory_worker.html', subcategory_id=subcategory.id)
        else:
            return redirect('subcategory_user.html', subcategory_id=subcategory.id)


    # Render different templates based on role
    context = {
        'subcategory': subcategory,
        'workers': workers,
        'testimonials': testimonials,
        'sessions': sessions,
        'user_profile': user_profile
    }

    if user_profile.role == 'worker':
        return render(request, 'subcategory_worker.html', context)
    else:
        return render(request, 'subcategory_user.html', context)
 
@login_required
def join_service_category(request, subcategory_id):
    subcategory = SubCategory.objects.get(id=subcategory_id)
    user_profile = UserProfile.objects.get(user=request.user)

    # Check if the worker is not already joined to the subcategory
    if user_profile not in subcategory.workers.all():
        # Add the worker to the subcategory
        subcategory.workers.add(user_profile)

    # Redirect to the same subcategory page
    return redirect('subcategory_detail', subcategory_id=subcategory.id)

def success(request):
    return render(request, 'success.html')

def worker(request):
    return render(request, 'worker.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                response = redirect('main:home')  # Redirect to the home page for both roles

                # Set last login cookie
                response.set_cookie('last_login', str(datetime.datetime.now()))

                return response  # Redirect to the same homepage for both roles

            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Save the user and set their password
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password1'])
                user.save()

                # Get role from POST data and create UserProfile
                role = request.POST.get('role')
                UserProfile.objects.create(user=user, role=role)

                messages.success(request, "Registration successful. You can now log in.")
                return redirect('main:login')
            except IntegrityError:
                # If username already exists, show an error message
                messages.error(request, "The username is already taken. Please choose a different one.")
                return redirect('main:register')
        else:
            # Form is invalid
            messages.error(request, "There were some errors in your form. Please check the details.")
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})

def logout(request):
    auth_logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response

def error(request):
    return render(request, 'error.html')

@login_required
def discounts(request):
    return render(request, 'discounts.html', {
        'vouchers': Voucher.objects.all(),
        'promos': Promo.objects.all(),
        'user': request.user.userprofile
    })


def manageorder(request):
    return render(request, 'manageorder.html')

def managejob(request):
    return render(request, 'managejob.html')

def myorder(request):
    return render(request, 'myorder.html')

def profile(request):
    return render(request, 'profile.html')

@login_required(login_url='/login/')
def mypay(request):
    user_profile = UserProfile.objects.get(user=request.user)
    transactions = user_profile.transactions.order_by('-timestamp')

    context = {
        'balance': user_profile.mypay_balance,
        'transactions': transactions,
    }
    return render(request, 'mypay.html', context)

@login_required
def transact(request):
    if request.method == "POST":
        transaction_type = request.POST.get("transaction_type")
        amount = Decimal(request.POST.get("amount", 0))

        # Retrieve the user's profile
        user_profile = UserProfile.objects.get(user=request.user)

        if transaction_type == "Deposit":
            # Add to balance
            user_profile.mypay_balance += amount
            user_profile.save()
            messages.success(request, f"Successfully deposited Rp {amount:.2f}.")
        elif transaction_type == "Withdraw":
            if user_profile.mypay_balance >= amount:
                # Deduct from balance
                user_profile.mypay_balance -= amount
                user_profile.save()
                messages.success(request, f"Successfully withdrew Rp {amount:.2f}.")
            else:
                messages.error(request, "Insufficient balance for withdrawal.")

    return redirect("main:mypay")

@login_required(login_url='/login/')
def mypay_transactions(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        transaction_type = request.POST.get('transaction_type')

        if transaction_type == 'TopUp':
            amount = float(request.POST.get('amount', 0))
            if amount > 0:
                user_profile.mypay_balance += amount
                user_profile.save()
                MyPayTransaction.objects.create(
                    user_profile=user_profile,
                    transaction_type='TopUp',
                    amount=amount
                )
                messages.success(request, "Top Up successful.")
            else:
                messages.error(request, "Invalid amount.")

        elif transaction_type == 'Withdrawal':
            amount = float(request.POST.get('amount', 0))
            if amount > 0 and user_profile.mypay_balance >= amount:
                user_profile.mypay_balance -= amount
                user_profile.save()
                MyPayTransaction.objects.create(
                    user_profile=user_profile,
                    transaction_type='Withdrawal',
                    amount=amount
                )
                messages.success(request, "Withdrawal successful.")
            else:
                messages.error(request, "Insufficient balance or invalid amount.")

        elif transaction_type == 'Transfer':
            recipient_phone = request.POST.get('recipient_phone')
            amount = float(request.POST.get('amount', 0))
            try:
                recipient_user = UserProfile.objects.get(user__username=recipient_phone)
                if amount > 0 and user_profile.mypay_balance >= amount:
                    user_profile.mypay_balance -= amount
                    recipient_user.mypay_balance += amount
                    user_profile.save()
                    recipient_user.save()
                    MyPayTransaction.objects.create(
                        user_profile=user_profile,
                        transaction_type='Transfer',
                        amount=-amount
                    )
                    MyPayTransaction.objects.create(
                        user_profile=recipient_user,
                        transaction_type='Transfer',
                        amount=amount
                    )
                    messages.success(request, "Transfer successful.")
                else:
                    messages.error(request, "Insufficient balance or invalid amount.")
            except UserProfile.DoesNotExist:
                messages.error(request, "Recipient not found.")

        return redirect('main:mypay')

    # Render the MyPay Transactions form on GET request
    service_sessions = ServiceSession.objects.filter(user=request.user) if hasattr(request.user, 'service_sessions') else []
    context = {
        'user': request.user,
        'balance': user_profile.mypay_balance,
        'date': now(),
        'service_sessions': service_sessions,
    }
    return render(request, 'mypay_transactions.html', context)
    
@login_required(login_url='/login/')
def service_jobs(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # Ensure the worker only sees jobs for their registered subcategories
    # and orders that are 'Looking for Nearby Worker'
    available_orders = ServiceOrder.objects.filter(
        subcategory__in=user_profile.subcategories.all(),
        status='Looking for Nearby Worker'
    )

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = ServiceOrder.objects.get(id=order_id)
            if order.status == 'Looking for Nearby Worker':
                order.worker = user_profile
                order.status = 'Waiting for Worker to Depart'
                order.save()
                messages.success(request, "Order accepted successfully.")
            else:
                messages.error(request, "Order is no longer available.")
        except ServiceOrder.DoesNotExist:
            messages.error(request, "Order not found.")
        return redirect('main:service_jobs')

    context = {
        'available_orders': available_orders,
    }
    return render(request, 'service_jobs.html', context)

@login_required(login_url='/login/')
def service_job_status(request):
    user_profile = UserProfile.objects.get(user=request.user)

    # Fetch active orders for the worker
    active_orders = ServiceOrder.objects.filter(
        worker=user_profile
    ).exclude(status__in=['Order Completed', 'Order Canceled'])

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        try:
            order = ServiceOrder.objects.get(id=order_id, worker=user_profile)
            if action == 'Arrived at Location' and order.status == 'Waiting for Worker to Depart':
                order.status = 'Worker Arrived at Location'
            elif action == 'Providing Service' and order.status == 'Worker Arrived at Location':
                order.status = 'Service in Progress'
            elif action == 'Service Completed' and order.status == 'Service in Progress':
                order.status = 'Order Completed'
                # Handle automatic payment transfer to worker (Trigger 4)
                order.worker.mypay_balance += order.total_payment
                order.worker.save()
                MyPayTransaction.objects.create(
                    user_profile=order.worker,
                    transaction_type='ServicePayment',
                    amount=order.total_payment
                )
            else:
                messages.error(request, "Invalid action.")
                return redirect('main:service_job_status')
            order.save()
            messages.success(request, f"Order status updated to {order.status}.")
        except ServiceOrder.DoesNotExist:
            messages.error(request, "Order not found.")
        return redirect('main:service_job_status')

    context = {
        'active_orders': active_orders,
    }
    return render(request, 'service_job_status.html', context)

@login_required(login_url='/login/')
def managejob(request):
    # Get worker's subcategories
    user_profile = UserProfile.objects.get(user=request.user)
    worker_subcategories = user_profile.subcategories.all()

    # Filter categories and subcategories
    selected_category = request.GET.get('category')
    selected_subcategory = request.GET.get('subcategory')

    categories = ServiceCategory.objects.filter(subcategories__in=worker_subcategories).distinct()
    subcategories = SubCategory.objects.filter(id__in=worker_subcategories)

    orders = ServiceOrder.objects.filter(
        subcategory__in=worker_subcategories, 
        status='Looking for Nearby Worker'
    )

    if selected_category:
        orders = orders.filter(subcategory__category_id=selected_category)
    if selected_subcategory:
        orders = orders.filter(subcategory_id=selected_subcategory)

    context = {
        'categories': categories,
        'subcategories': subcategories,
        'orders': orders,
    }
    return render(request, 'manage_job.html', context)

@login_required
def accept_order(request, order_id):
    # Worker accepts the order
    order = get_object_or_404(ServiceOrder, id=order_id, status='Looking for Nearby Worker')
    order.status = 'Waiting for Nearby Worker'
    order.worker = request.user.userprofile
    order.save()
    messages.success(request, "Order accepted successfully!")
    return redirect('main:managejob')

@login_required(login_url='/login/')
def manage_order_status(request):
    user_profile = request.user.userprofile

    # Ensure the user is a worker
    if user_profile.role != 'worker':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('main:home')

    # Fetch orders assigned to the worker
    orders = ServiceOrder.objects.filter(worker=user_profile).exclude(status__in=['Order Completed', 'Order Canceled'])

    # Update order status if a POST request is made
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        try:
            order = ServiceOrder.objects.get(id=order_id, worker=user_profile)
            if action == 'Arrived at Location' and order.status == 'Waiting for Worker to Depart':
                order.status = 'Worker Arrived at Location'
            elif action == 'Providing Service' and order.status == 'Worker Arrived at Location':
                order.status = 'Service in Progress'
            elif action == 'Service Completed' and order.status == 'Service in Progress':
                order.status = 'Order Completed'
            else:
                messages.error(request, "Invalid action or order status.")
                return redirect('main:manage_order_status')
            order.save()
            messages.success(request, f"Order status updated to: {order.status}.")
        except ServiceOrder.DoesNotExist:
            messages.error(request, "Order not found or not assigned to you.")
        return redirect('main:manage_order_status')

    context = {
        'orders': orders,
    }
    return render(request, 'manage_order_status.html', context)

@login_required(login_url='/login/')
def AddTestimonial(req, subcategory_id):
    '''Add a Testimonial to Subcategory'''
    SubCat = SubCategory.objects.get(id=subcategory_id)

    if req.method == 'POST':

        '''Fetch Rating and Comment'''
        Rating = req.POST.get('rating') 
        Comment = req.POST.get('comment') 

        '''Ensure Data'''
        if Rating and Comment:
            Testimonial.objects.create(
                rating=int(Rating),
                comment=Comment,
                subcategory=SubCat,
                user=req.user
            )
            return redirect(f'/subcategory/{subcategory_id}/')

    return render(req, 'add_testimonial.html', {'subcategory': SubCat})
