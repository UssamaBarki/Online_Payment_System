from .forms import RegistrationForm
from .models import OnlineAccount
from decimal import Decimal
from django.db import IntegrityError
from payapp.utils import fetch_exchange_rates
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from .forms import CustomAuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from register.forms import AdminRegistrationForm
import logging


logger = logging.getLogger(__name__)

def register_user(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Attempt to create the new user
                user = form.save(commit=False)
                raw_password = form.cleaned_data['password']
                user.set_password(raw_password)
                user.save()

                # Process the selected currency and set initial balance
                selected_currency = form.cleaned_data['currency']
                baseline = 1000  # Baseline amount in GBP

                # Call REST API for currency conversion
                converted_balance = fetch_exchange_rates('GBP', selected_currency, float(baseline))

                # Ensure we use the converted balance if available
                initial_balance = Decimal(str(converted_balance)) if converted_balance is not None else Decimal(str(baseline))

                # Ensure any old deleted account is removed before creating a new one
                OnlineAccount.objects.filter(user=user).delete()

                # Create the OnlineAccount for the new user
                OnlineAccount.objects.create(
                    user=user,
                    currency=selected_currency,
                    balance=initial_balance
                )
                messages.success(request, "User registered successfully! Please log in.")
                return redirect('login')

            except IntegrityError:
                messages.error(request, "A user with this username or email already exists.")
        else:
            # General form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = RegistrationForm()

    return render(request, 'register/register.html', {'form': form})


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'register/login.html'

    def form_invalid(self, form):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')

        user = authenticate(self.request, username=username, password=password)
        if user is None:
            try:
                User.objects.get(username=username)
                error_message = "Password incorrect."
            except User.DoesNotExist:
                error_message = "No user account found with this username."
        else:
            error_message = "Invalid login credentials."

        return self.render_to_response(self.get_context_data(form=form, error_message=error_message))


def admin_required(user):
    return user.is_superuser


def admin_login(request):
    logger.info(f"Request Method: {request.method}")

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            if user.is_staff:
                logger.info(f"Admin {username} authenticated successfully")
                login(request, user)
                return redirect('admin_dashboard')
            else:
                logger.warning(f"User {username} is not an admin.")
                messages.error(request, "You are not an admin.")
        else:
            logger.warning(f"Login failed for username: {username}")
            messages.error(request, "Invalid username or password.")

    return render(request, 'register/admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def register_superuser(request):
    if request.method == "POST":
        form = AdminRegistrationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' is already taken!")
                print(f"DEBUG: Username '{username}' already exists in DB")
            elif User.objects.filter(email=email).exists():
                messages.error(request, f"Email '{email}' is already in use!")
                print(f"DEBUG: Email '{email}' already exists in DB")
            else:
                try:
                    # Create new superuser
                    user = form.save(commit=False)
                    user.is_staff = True
                    user.is_superuser = True
                    user.set_password(form.cleaned_data['password'])
                    user.save()

                    messages.success(request, "New superuser registered successfully!")
                    print("DEBUG: Superuser created successfully")
                    return redirect('admin_dashboard')

                except IntegrityError:
                    messages.error(request, f"User with username '{username}' or email '{email}' already exists!")
                    print(f"DEBUG: IntegrityError - User '{username}' or '{email}' already exists in DB")

        else:
            # Log form errors and pass them to messages framework
            print(f"DEBUG: Form validation errors -> {form.errors.as_json()}")
            for field, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"{field.capitalize()}: {error}")

    else:
        form = AdminRegistrationForm()

    return render(request, 'register/register_superuser.html', {"form": form})