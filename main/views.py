from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import LoginForm
from .models import UserProfile
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

@login_required
def home(request):
    return render(request, 'home.html')
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
                response = redirect('main:home')  # Default redirect to home page

                # Set last login cookie
                response.set_cookie('last_login', str(datetime.datetime.now()))

                # Role-based redirection after login
                if hasattr(user, 'userprofile') and user.userprofile.role == 'user':
                    return redirect('main:success')  # Host dashboard
                else:
                    return redirect('main:worker')  # Worker (guest) dashboard

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