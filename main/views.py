from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import LoginForm
from .models import UserProfile,ServiceCategory,SubCategory,Testimonial
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q

@login_required(login_url='/login/')
def home(request):
    # Retrieve the logged-in user's profile to check their role
    user_profile = UserProfile.objects.get(user=request.user)
    user_role = user_profile.role

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

    # Determine which template to render based on the user's role
    if user_role == 'user':
        return render(request, 'success.html', {'categories': categories, 'search_term': search_term})
    elif user_role == 'worker':
        return render(request, 'success.html', {'categories': categories, 'search_term': search_term})
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

def discounts(request):
    return render(request, 'discounts.html')

def manageorder(request):
    return render(request, 'manageorder.html')

def managejob(request):
    return render(request, 'managejob.html')

def myorder(request):
    return render(request, 'myorder.html')

def mypay(request):
    return render(request, 'mypay.html')

def profile(request):
    return render(request, 'profile.html')