docs/user-auth-flow.md

# User Authentication Flow — Afrola.ai (Django)

## Purpose
Define how users register, login, manage sessions, and control access using Django's built-in authentication system.

## Flow Overview
Register → Email Verify → Login → Session → Protected Views
↓ ↓ ↓ ↓ ↓
User Form Token JWT/Auth Cookie Decorator

text

## Architecture Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Custom User Model | `accounts/models.py` | Extended user with UUID, email auth |
| Registration Form | `accounts/forms.py` | User signup validation |
| Auth Views | `accounts/views.py` | Register, login, profile |
| Auth URLs | `accounts/urls.py` | Authentication routes |
| Templates | `templates/accounts/` | Login, register, profile forms |
| Decorators | `accounts/decorators.py` | Role/permission checks |
| Context Processor | `dashboard/context_processors.py` | User data for all templates |
| Signals | `accounts/signals.py` | Post-registration actions |

## Required Files

### Backend Files
backend/accounts/
├── init.py # ✅
├── admin.py # ✅ User admin interface
├── apps.py # ✅ App config
├── models.py # ✅ Custom User model
├── urls.py # ⏳ Auth URLs
├── views.py # ⏳ Registration, profile views
├── forms.py # ⏳ Registration, login forms
├── decorators.py # ⏳ Role/permission decorators
├── utils.py # ⏳ Email verification helpers
├── signals.py # ⏳ Post-registration signals
└── tests.py # ⏳ Auth tests

backend/config/
├── settings.py # ✅ Auth settings (LOGIN_URL, etc.)
└── urls.py # ✅ Include auth URLs

backend/templates/accounts/
├── login.html # ⏳ Login form
├── register.html # ⏳ Registration form
├── profile.html # ⏳ User profile
├── password_reset_form.html # ⏳ Password reset request
├── password_reset_email.html # ⏳ Reset email template
├── password_reset_confirm.html # ⏳ Set new password
└── password_reset_done.html # ⏳ Reset confirmation

backend/templates/dashboard/
└── index.html # ⏳ Protected dashboard (requires login)

text

## Implementation Plan

### Batch 1: Custom User Model (✅ Already done)
- UUID primary key
- Email as username field
- Subscription tier field
- Usage tracking fields
- Created/updated timestamps

### Batch 2: Registration Flow
**Files to create:**
- `accounts/forms.py` - UserRegistrationForm
- `accounts/views.py` - register view
- `accounts/utils.py` - generate_verification_token
- `accounts/signals.py` - post_save signal for welcome email
- `templates/accounts/register.html`
- `templates/accounts/verification_email.html`

**Flow:**
1. User submits email, full_name, password
2. Form validates input
3. User created with `is_active=False`
4. Verification token generated
5. Email sent with verification link
6. User clicks link → `is_active=True`
7. Auto-assign free subscription plan
8. Redirect to login

### Batch 3: Login & Session
**Files to create:**
- `templates/accounts/login.html`
- `accounts/views.py` - custom_login (optional, or use Django's built-in)

**Flow:**
1. User enters credentials
2. Django authenticates via `django.contrib.auth.authenticate()`
3. Session created via `django.contrib.auth.login()`
4. User redirected to dashboard

**Settings to verify:**

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

Batch 4: Protected Views
Files to create:

accounts/decorators.py - role_required, subscription_required

dashboard/context_processors.py - user_subscription_info

Usage:

python
from django.contrib.auth.decorators import login_required
from accounts.decorators import subscription_required

@login_required
@subscription_required('pro')
def premium_feature(request):
    pass

Batch 5: Password Reset
Files to create:

templates/accounts/password_reset_form.html

templates/accounts/password_reset_email.html

templates/accounts/password_reset_confirm.html

templates/accounts/password_reset_done.html

URLs to add in accounts/urls.py:

python
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset_form.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]
Batch 6: Email Verification
Files to create:

accounts/utils.py - generate_token, send_verification_email

templates/accounts/verification_email.html

Implementation:

python
# accounts/utils.py
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_url = f"{settings.FRONTEND_URL}/verify/{uid}/{token}/"
    # Send email with verification_url
Batch 7: Profile Management
Files to create:

templates/accounts/profile.html

accounts/forms.py - UserProfileForm

accounts/views.py - profile_view, profile_update

Features:

Update full_name

Change password

View subscription status

View usage statistics

Manage API keys

Download data export

Batch 8: Role-Based Permissions
Files to create:

accounts/decorators.py - admin_required, staff_required

accounts/utils.py - has_permission helper

User Roles:

Role	Permission
User	Basic access, create jobs, view own data
Pro User	All user + higher limits, priority queue
Staff	Manage users, view all jobs
Admin	Full system access, manage plans

Batch 9: Social Authentication (Optional)
Files to create:

Install django-allauth

accounts/social_auth.py - custom adapters

templates/accounts/social_login.html

Providers:

Google

GitHub

LinkedIn (for enterprise)

Batch 10: Session Security
Settings for production:

python
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = True
Dependencies
Django's built-in auth contrib package

django-allauth (optional, for social auth)

No external packages needed for core auth (batteries included)

Environment Variables
bash
# Email settings (for verification and password reset)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@afrola.ai

# Frontend URL for email links
FRONTEND_URL=http://localhost:3000

# Session security (production)
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
Verification Checklist
User can register with email/password

Verification email sent and works

User can login after verification

Session persists across pages

Logout works

Protected routes require login

Password reset works

User profile editable

Admin can manage users in Django admin

Subscription required decorator works

Email templates render correctly

Next Steps After Auth
Once authentication is working, proceed to:

docs/file-upload-flow.md - Allow users to upload media

docs/subscription-flow.md - Implement paid tiers

docs/celery-queue-flow.md - Async processing

docs/api-rest-flow.md - Programmatic access

Related Documentation
docs/subscription-flow.md - Plan assignment after registration

docs/file-upload-flow.md - Authenticated file uploads

docs/database-schema.md - User model schema

docs/api-rest-flow.md - JWT authentication for API