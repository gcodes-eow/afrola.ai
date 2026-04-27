# backend/config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv
from config.logging import LOGGING

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-opfiofyf06@%5@22_r$zx45$an((i(zp%kcyn)x@k%ft^_89yz')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'corsheaders',
    'django_celery_results',
    
    # My apps
    'accounts',
    'jobs',
    'ai_engine',
    'pricing',
    'payments',
    'dashboard',
    'api',
]

# Add these settings
AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.user_subscription_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Database configuration from environment variables
if os.getenv('DB_ENGINE') == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE'),
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings (only if corsheaders is installed)
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all origins only in development
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Redis Configuration (for Celery)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'  # Store results in Django database
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'True') == 'True'  # Sync in dev

# Celery Queue Routes
CELERY_TASK_ROUTES = {
    'ai_engine.tasks.process_text_to_text_task': {'queue': 'high_priority'},
    'ai_engine.tasks.process_audio_to_text_task': {'queue': 'high_priority'},
    'ai_engine.tasks.process_video_to_text_task': {'queue': 'high_priority'},
    'ai_engine.tasks.process_translation_task': {'queue': 'high_priority'},
    'ai_engine.tasks.create_dubbed_audio_task': {'queue': 'high_priority'},
    'ai_engine.tasks.create_dubbed_video_task': {'queue': 'high_priority'},
    'ai_engine.tasks.process_youtube_dubbing_task': {'queue': 'default'},
    'ai_engine.tasks.process_subtitle_generation_task': {'queue': 'low_priority'},
    'ai_engine.tasks.cleanup_old_jobs_task': {'queue': 'low_priority'},
    'ai_engine.tasks.health_check_task': {'queue': 'scheduled'},
    'accounts.tasks.reset_monthly_usage_task': {'queue': 'scheduled'},
}

# Queue priorities (0-9, higher = more urgent)
CELERY_TASK_DEFAULT_PRIORITY = 5
CELERY_TASK_QUEUE_MAX_PRIORITY = 10

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@afrola.ai')

# Stripe Payment Configuration
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Airtel Mobile Money Configuration
AIRTEL_MONEY_ENABLED = os.getenv('AIRTEL_MONEY_ENABLED', 'False') == 'True'
AIRTEL_MONEY_API_URL = os.getenv('AIRTEL_MONEY_API_URL', 'https://openapi.airtel.africa')
AIRTEL_MONEY_CLIENT_ID = os.getenv('AIRTEL_MONEY_CLIENT_ID')
AIRTEL_MONEY_CLIENT_SECRET = os.getenv('AIRTEL_MONEY_CLIENT_SECRET')
AIRTEL_MONEY_API_KEY = os.getenv('AIRTEL_MONEY_API_KEY')
AIRTEL_MONEY_PIN = os.getenv('AIRTEL_MONEY_PIN')
AIRTEL_MONEY_COUNTRY = os.getenv('AIRTEL_MONEY_COUNTRY', 'UG')
AIRTEL_MONEY_CURRENCY = os.getenv('AIRTEL_MONEY_CURRENCY', 'UGX')
AIRTEL_MONEY_WEBHOOK_SECRET = os.getenv('AIRTEL_MONEY_WEBHOOK_SECRET')

# MTN Mobile Money Configuration
MTN_MONEY_ENABLED = os.getenv('MTN_MONEY_ENABLED', 'False') == 'True'
MTN_MONEY_API_URL = os.getenv('MTN_MONEY_API_URL', 'https://sandbox.mtn.com/collection/v1_0')
MTN_MONEY_SUBSCRIPTION_KEY = os.getenv('MTN_MONEY_SUBSCRIPTION_KEY')
MTN_MONEY_API_USER = os.getenv('MTN_MONEY_API_USER')
MTN_MONEY_API_KEY = os.getenv('MTN_MONEY_API_KEY')
MTN_MONEY_PIN = os.getenv('MTN_MONEY_PIN')
MTN_MONEY_COUNTRY = os.getenv('MTN_MONEY_COUNTRY', 'UG')
MTN_MONEY_CURRENCY = os.getenv('MTN_MONEY_CURRENCY', 'UGX')
MTN_MONEY_WEBHOOK_SECRET = os.getenv('MTN_MONEY_WEBHOOK_SECRET')
MTN_MONEY_CALLBACK_URL = os.getenv('MTN_MONEY_CALLBACK_URL', 'https://your-domain.com/api/webhooks/mtn/')

# Mobile Money Common Settings
MOBILE_MONEY_ENVIRONMENT = os.getenv('MOBILE_MONEY_ENVIRONMENT', 'sandbox')
MOBILE_MONEY_TIMEOUT = int(os.getenv('MOBILE_MONEY_TIMEOUT', 30))
MOBILE_MONEY_MAX_RETRIES = int(os.getenv('MOBILE_MONEY_MAX_RETRIES', 3))
MOBILE_MONEY_RETRY_DELAY = int(os.getenv('MOBILE_MONEY_RETRY_DELAY', 5))

# Payment Providers Priority
PAYMENT_PROVIDERS = os.getenv('PAYMENT_PROVIDERS', 'stripe,airtel_money,mtn_money').split(',')

# Frontend URL (for email links and CORS)
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

# AWS S3 Storage (for production)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

# Configure S3 for static/media files in production (uncomment if using S3)
if AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Security Settings (for production)
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# API Configuration
API_RATE_LIMIT_PER_MINUTE = int(os.getenv('API_RATE_LIMIT_PER_MINUTE', 60))
API_RATE_LIMIT_PER_DAY = int(os.getenv('API_RATE_LIMIT_PER_DAY', 1000))

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# File Upload Limits
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 500))
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240
DATA_UPLOAD_MAX_NUMBER_FILES = 100

# Allowed file types
ALLOWED_AUDIO_TYPES = os.getenv('ALLOWED_AUDIO_TYPES', 'mp3,wav,m4a,ogg').split(',')
ALLOWED_VIDEO_TYPES = os.getenv('ALLOWED_VIDEO_TYPES', 'mp4,avi,mov,mkv').split(',')

# File Upload Tier Limits
FREE_MAX_UPLOAD_SIZE_MB = int(os.getenv('FREE_MAX_UPLOAD_SIZE_MB', 100))
PRO_MAX_UPLOAD_SIZE_MB = int(os.getenv('PRO_MAX_UPLOAD_SIZE_MB', 500))
ENTERPRISE_MAX_UPLOAD_SIZE_MB = int(os.getenv('ENTERPRISE_MAX_UPLOAD_SIZE_MB', 2000))

FREE_MAX_DURATION_SECONDS = int(os.getenv('FREE_MAX_DURATION_SECONDS', 600))
PRO_MAX_DURATION_SECONDS = int(os.getenv('PRO_MAX_DURATION_SECONDS', 3600))
ENTERPRISE_MAX_DURATION_SECONDS = int(os.getenv('ENTERPRISE_MAX_DURATION_SECONDS', 7200))

# YouTube API (optional)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Custom Training Models (optional)
MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', '/tmp/afrola_models')

# Mobile Money Transaction Settings
MINIMUM_PAYMENT_AMOUNT = int(os.getenv('MINIMUM_PAYMENT_AMOUNT', 1000))  # UGX
MAXIMUM_PAYMENT_AMOUNT = int(os.getenv('MAXIMUM_PAYMENT_AMOUNT', 1000000))  # UGX
MOBILE_MONEY_DESCRIPTION = os.getenv('MOBILE_MONEY_DESCRIPTION', 'Afrola.ai Subscription Payment')

# Payment Timeouts (in seconds)
PAYMENT_EXPIRY_TIME = int(os.getenv('PAYMENT_EXPIRY_TIME', 300))
PAYMENT_CONFIRMATION_TIMEOUT = int(os.getenv('PAYMENT_CONFIRMATION_TIMEOUT', 60))

# Webhook Security
WEBHOOK_ALLOWED_IPS = os.getenv('WEBHOOK_ALLOWED_IPS', '127.0.0.1,::1').split(',')
WEBHOOK_SIGNATURE_HEADER = os.getenv('WEBHOOK_SIGNATURE_HEADER', 'X-Signature')

# Test Phone Numbers (for development)
TEST_AIRTEL_NUMBER = os.getenv('TEST_AIRTEL_NUMBER', '256700000000')
TEST_MTN_NUMBER = os.getenv('TEST_MTN_NUMBER', '256780000000')
TEST_AMOUNT = int(os.getenv('TEST_AMOUNT', 1000))

# Cache Settings
CACHE_TTL_MOBILE_MONEY_STATUS = int(os.getenv('CACHE_TTL_MOBILE_MONEY_STATUS', 30))

# Simplified Cache Configuration - Local memory cache only (no Redis to avoid errors)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'afrola-cache',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# Session configuration (use database for sessions, not cache - more reliable)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True

# CSRF settings
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://localhost:3000').split(',')
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True

# Auth URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Auth backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Security headers
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # 1 year in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Admin settings
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

# Custom settings
SITE_NAME = 'Afrola.ai'
SITE_DESCRIPTION = 'AI-powered translation platform for Luganda and English'
SITE_URL = FRONTEND_URL