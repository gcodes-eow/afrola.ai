# backend/accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from .models import User
from .forms import UserRegistrationForm, UserProfileForm
from .utils import send_verification_email


def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(user, request)
            messages.success(
                request,
                'Registration successful! Please check your email to verify your account.'
            )
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def verify_email_view(request, uidb64, token):
    """Verify user email via token link"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.is_active = True
        user.email_verification_token = None
        user.save()
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Verification link is invalid or has expired.')
        return redirect('accounts:login')


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if not user.is_active:
                messages.warning(
                    request,
                    'Your account is not verified. Please check your email for the verification link.'
                )
                return render(request, 'accounts/login.html')

            login(request, user)

            if not remember_me:
                request.session.set_expiry(0)  # Browser session
            else:
                request.session.set_expiry(86400 * 30)  # 30 days

            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html')


@login_required
def profile_view(request):
    """Display user profile"""
    context = {
        'user': request.user,
        'subscription': getattr(request.user, 'subscription', None),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_update_view(request):
    """Update user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def resend_verification_view(request):
    """Resend verification email"""
    if request.user.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('dashboard:index')

    send_verification_email(request.user, request)
    messages.success(request, 'Verification email sent. Please check your inbox.')
    return redirect('accounts:profile')