docs/api-rest-flow.md

# API REST Flow — Afrola.ai (Django REST Framework)

## Purpose
Define the REST API for programmatic access to Afrola.ai services, enabling third-party integrations, mobile apps, and automated workflows for transcription, translation, and dubbing services.

## Overview
Client → API Request → Authentication → Rate Limit → View → Serializer → Response
↓ ↓ ↓ ↓ ↓ ↓ ↓
Mobile DRF Router API Key/ Throttling Business JSON/XML JSON/XML
App/JWT + ViewSet JWT Classes Logic Output Client

text

## Architecture Components

| Component | Location | Purpose |
|-----------|----------|---------|
| DRF Configuration | `config/settings.py` | DRF settings, auth classes |
| API Router | `api/urls.py` | Route all API endpoints |
| ViewSets | `api/views.py` | CRUD operations for resources |
| Serializers | `api/serializers.py` | Request/response validation |
| Permissions | `api/permissions.py` | API key, user ownership |
| Throttling | `api/throttling.py` | Rate limiting per user |
| API Key Auth | `api/authentication.py` | API key validation |
| API Key Model | `api/models.py` | Store API keys |
| Pagination | `api/pagination.py` | Custom pagination classes |

## Required Files

### Core API Files
backend/api/
├── init.py # ✅
├── apps.py # ✅ App config
├── urls.py # ⏳ API routes (router)
├── views.py # ⏳ ViewSets
├── serializers.py # ⏳ Serializers
├── permissions.py # ⏳ Custom permissions
├── authentication.py # ⏳ API key auth
├── throttling.py # ⏳ Rate limiting
├── pagination.py # ⏳ Custom pagination
├── models.py # ✅ APIKey model
├── admin.py # ✅ APIKey admin
├── tests.py # ⏳ API tests
└── openapi.py # ⏳ Custom OpenAPI schema

text

### Supporting Files
backend/config/
├── settings.py # ✅ DRF settings
├── urls.py # ✅ Include api.urls
└── openapi.py # ⏳ OpenAPI configuration

backend/accounts/
├── serializers.py # ⏳ User serializer
├── permissions.py # ⏳ Account permissions
└── views.py # ⏳ User API views

backend/jobs/
├── serializers.py # ⏳ Job serializer
├── permissions.py # ⏳ Job ownership
└── views.py # ⏳ Job API views

backend/ai_engine/
├── serializers.py # ⏳ Task/voice serializers
└── views.py # ⏳ Voice list/preview API

backend/payments/
├── serializers.py # ⏳ Subscription serializers
└── views.py # ⏳ Plan API views

text

## Implementation Plan

### Batch 1: DRF Setup
**Files to create:**
- `config/settings.py` - Add DRF configuration
- `config/urls.py` - Include API routes
- `api/apps.py` - API app config

**Settings Configuration:**
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'api',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'api.authentication.APIKeyAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'api.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'burst': '60/min',
        'upload': '50/hour',
        'download': '200/hour',
    },
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.CustomPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}
Batch 2: API Key Authentication
Files to create:

api/models.py - APIKey model (already exists, verify)

api/authentication.py - APIKeyAuthentication class

api/permissions.py - HasValidAPIKey permission

API Key Model (verify/update):

python
class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True)
    key_prefix = models.CharField(max_length=10)
    permissions = models.JSONField(default=list)  # ['read', 'write', 'admin']
    rate_limit_per_minute = models.IntegerField(default=60)
    rate_limit_per_day = models.IntegerField(default=1000)
    last_used_at = models.DateTimeField(null=True)
    total_requests = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
Batch 3: ViewSets & Serializers
Files to create:

api/serializers.py - All serializers

api/views.py - All ViewSets

api/urls.py - Router configuration

ViewSets to Implement:

ViewSet	Endpoint	Description
UserViewSet	/api/users/	User profile CRUD
JobViewSet	/api/jobs/	Job management
ResultViewSet	/api/results/	Result download
PlanViewSet	/api/plans/	Subscription plans
SubscriptionViewSet	/api/subscriptions/	User subscriptions
VoiceViewSet	/api/voices/	Available voices
WebhookViewSet	/api/webhooks/	Webhook management
APIKeyViewSet	/api/keys/	API key management
UsageViewSet	/api/usage/	Usage statistics
Batch 4: Custom Permissions
Files to create:

api/permissions.py - All permission classes

Permission Classes:

python
class IsOwner(permissions.BasePermission):
    """Allow access only to owner of the object"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class HasValidAPIKey(permissions.BasePermission):
    """Allow access only with valid API key"""
    def has_permission(self, request, view):
        return hasattr(request, 'api_key') and request.api_key.is_active

class HasSubscriptionTier(permissions.BasePermission):
    """Allow access based on subscription tier"""
    def has_permission(self, request, view):
        required_tier = getattr(view, 'required_tier', None)
        if not required_tier:
            return True
        return request.user.subscription.tier == required_tier

class HasJobOwnership(permissions.BasePermission):
    """Allow access only to job owner"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
Batch 5: Rate Limiting
Files to create:

api/throttling.py - Custom throttle classes

Throttle Classes:

python
class BurstRateThrottle(UserRateThrottle):
    rate = '60/min'

class SubscriptionBasedThrottle(BaseThrottle):
    def get_rate(self, request):
        if request.user.subscription.tier == 'free':
            return '10/min'
        elif request.user.subscription.tier == 'pro':
            return '60/min'
        return '300/min'

class APIKeyRateThrottle(BaseThrottle):
    def get_rate(self, request):
        if hasattr(request, 'api_key'):
            return f"{request.api_key.rate_limit_per_minute}/min"
        return '60/min'
Batch 6: API Documentation
Files to create:

config/openapi.py - OpenAPI schema config

api/openapi.py - Custom schema generation

Documentation URLs:

Swagger UI: http://localhost:8000/api/docs/

ReDoc: http://localhost:8000/api/redoc/

OpenAPI Schema: http://localhost:8000/api/schema/

API Endpoints
Authentication
Method	Endpoint	Description	Auth
POST	/api/auth/register/	Register new user	None
POST	/api/auth/login/	Obtain JWT token	None
POST	/api/auth/logout/	Revoke token	JWT
POST	/api/auth/refresh/	Refresh JWT	None
GET	/api/auth/me/	Get current user	JWT/API Key
PUT	/api/auth/me/	Update profile	JWT/API Key
API Keys
Method	Endpoint	Description	Auth
GET	/api/keys/	List API keys	JWT
POST	/api/keys/	Create API key	JWT
DELETE	/api/keys/{id}/	Revoke API key	JWT
Jobs
Method	Endpoint	Description	Auth
GET	/api/jobs/	List user jobs	JWT/API Key
POST	/api/jobs/	Create job (file/YouTube)	JWT/API Key
GET	/api/jobs/{id}/	Get job details	JWT/API Key
DELETE	/api/jobs/{id}/	Cancel job	JWT/API Key
GET	/api/jobs/{id}/status/	Get progress	JWT/API Key
Dubbing-Specific Endpoints
Method	Endpoint	Description	Auth
GET	/api/voices/	List available voices	JWT/API Key
GET	/api/voices/{id}/preview/	Preview voice sample	JWT/API Key
POST	/api/jobs/{id}/regenerate/	Regenerate with different voice	JWT/API Key
GET	/api/jobs/{id}/preview/audio/	Get audio preview	JWT/API Key
GET	/api/jobs/{id}/preview/video/	Get video preview	JWT/API Key
Results
Method	Endpoint	Description	Format
GET	/api/jobs/{id}/transcript/	Download transcript	TXT/JSON
GET	/api/jobs/{id}/translation/	Download translation	TXT/JSON
GET	/api/jobs/{id}/subtitles/	Download subtitles	SRT/VTT
GET	/api/jobs/{id}/dubbed-audio/	Download dubbed audio	MP3/WAV
GET	/api/jobs/{id}/dubbed-video/	Download dubbed video	MP4
Pricing & Subscriptions
Method	Endpoint	Description	Auth
GET	/api/plans/	List subscription plans	None
GET	/api/subscription/	Get current subscription	JWT/API Key
POST	/api/subscription/	Create/update subscription	JWT
DELETE	/api/subscription/	Cancel subscription	JWT
Usage & Analytics
Method	Endpoint	Description	Auth
GET	/api/usage/	Get current usage stats	JWT/API Key
GET	/api/usage/history/	Get usage history	JWT/API Key
GET	/api/stats/	Get aggregated stats (admin)	JWT (Staff)
Webhooks
Method	Endpoint	Description	Auth
GET	/api/webhooks/	List webhook endpoints	JWT/API Key
POST	/api/webhooks/	Register webhook	JWT/API Key
DELETE	/api/webhooks/{id}/	Delete webhook	JWT/API Key
Request/Response Examples
Create Dubbing Job (File Upload)
http
POST /api/jobs/
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

{
    "file": <binary>,
    "job_type": "video_to_video",
    "source_language": "lg",
    "target_language": "en",
    "title": "My First Dubbed Video",
    "voice_model": "luganda_female_1",
    "add_background_music": true,
    "music_volume": 0.3,
    "generate_subtitles": true
}
Response:

json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "job_type": "video_to_video",
    "source_language": "lg",
    "target_language": "en",
    "created_at": "2024-01-15T10:30:00Z",
    "estimated_duration_seconds": 180,
    "estimated_cost_minutes": 5
}
Get Job Status with Progress
http
GET /api/jobs/550e8400-e29b-41d4-a716-446655440000/status/
Authorization: Bearer <jwt_token>
Response:

json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "progress": 45,
    "current_step": "synthesizing_speech",
    "steps": [
        {"name": "transcribing", "status": "completed", "progress": 100},
        {"name": "translating", "status": "completed", "progress": 100},
        {"name": "synthesizing_speech", "status": "in_progress", "progress": 60},
        {"name": "merging_audio", "status": "pending", "progress": 0}
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "estimated_remaining_seconds": 45
}
List Available Voices
http
GET /api/voices/?language=lg
Authorization: Bearer <jwt_token>
Response:

json
{
    "count": 4,
    "results": [
        {
            "id": "voice_001",
            "name": "Luganda Female - Grace",
            "language": "lg",
            "gender": "female",
            "accent": "Kampala",
            "preview_url": "/api/voices/voice_001/preview/",
            "is_premium": false
        },
        {
            "id": "voice_002",
            "name": "Luganda Male - John",
            "language": "lg",
            "gender": "male",
            "accent": "Gulu",
            "preview_url": "/api/voices/voice_002/preview/",
            "is_premium": false
        }
    ]
}
Get Dubbed Video Preview
http
GET /api/jobs/550e8400-e29b-41d4-a716-446655440000/preview/video/
Authorization: Bearer <jwt_token>
Response: (Binary video file, 30-second preview)

Authentication Methods
JWT Token (for web/mobile users)
http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
API Key (for third-party integrations)
http
X-API-Key: afrola_live_xxxxxxxxxxxxx
Session Cookie (for Django admin)
http
Cookie: sessionid=xxxxxxxxxxxxx
Rate Limits by Tier
Tier	Requests/Minute	Requests/Day	Concurrent Jobs	File Size Limit
Free	10	100	1	100 MB
Pro	60	1000	3	500 MB
Enterprise	300	10000	10	2000 MB
API Key	Custom	Custom	Custom	Custom
Error Responses
400 Bad Request
json
{
    "error": "validation_error",
    "message": "Invalid file type. Allowed: mp3, wav, mp4, mov",
    "fields": {
        "file": ["File too large", "Invalid format"],
        "source_language": ["Language not supported"]
    }
}
401 Unauthorized
json
{
    "error": "authentication_required",
    "message": "Valid API key or JWT required",
    "documentation_url": "https://docs.afrola.ai/api/authentication"
}
402 Payment Required
json
{
    "error": "quota_exceeded",
    "message": "Monthly limit exceeded. Upgrade to Pro plan",
    "upgrade_url": "https://afrola.ai/pricing",
    "remaining_minutes": 0
}
403 Forbidden
json
{
    "error": "permission_denied",
    "message": "You do not own this job",
    "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
404 Not Found
json
{
    "error": "not_found",
    "message": "Job with ID '550e8400-e29b-41d4-a716-446655440000' not found",
    "request_id": "req_abc123"
}
409 Conflict
json
{
    "error": "job_in_progress",
    "message": "Cannot cancel job that is already completed",
    "current_status": "completed"
}
429 Too Many Requests
json
{
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Try again in 45 seconds",
    "reset_at": "2024-01-15T10:31:00Z",
    "limit": "60/minute",
    "remaining": 0
}
500 Internal Error
json
{
    "error": "server_error",
    "message": "An unexpected error occurred",
    "request_id": "req_xxxxxxxxxx",
    "support_email": "support@afrola.ai"
}
URL Configuration
python
# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

router = DefaultRouter()
router.register(r'jobs', views.JobViewSet, basename='job')
router.register(r'plans', views.PlanViewSet, basename='plan')
router.register(r'keys', views.APIKeyViewSet, basename='apikey')
router.register(r'voices', views.VoiceViewSet, basename='voice')
router.register(r'webhooks', views.WebhookViewSet, basename='webhook')
router.register(r'usage', views.UsageViewSet, basename='usage')

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/me/', views.CurrentUserView.as_view(), name='current_user'),
    
    # Webhooks (no auth, signature verified)
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
    path('webhooks/mtn/', views.MTNWebhookView.as_view(), name='mtn_webhook'),
    path('webhooks/airtel/', views.AirtelWebhookView.as_view(), name='airtel_webhook'),
]

# api/urls_docs.py (separate for documentation)
urlpatterns += [
    path('docs/', include('drf_spectacular.urls')),
]
Settings Configuration
python
# config/settings.py

INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]

# CORS settings for API
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = ['accept', 'accept-encoding', 'authorization', 'content-type', 'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with', 'x-api-key']

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# DRF Spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Afrola.ai API',
    'DESCRIPTION': 'AI-powered translation and dubbing platform API for African languages',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
        'displayRequestDuration': True,
    },
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication endpoints'},
        {'name': 'jobs', 'description': 'Job management for translation/dubbing'},
        {'name': 'voices', 'description': 'Voice models for dubbing'},
        {'name': 'subscriptions', 'description': 'Plan and subscription management'},
        {'name': 'usage', 'description': 'Usage statistics and limits'},
        {'name': 'webhooks', 'description': 'Webhook endpoints'},
    ],
}
Dependencies
txt
# requirements.txt additions
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
drf-spectacular==0.27.0
django-filter==23.5
django-cors-headers==4.3.1
Environment Variables
bash
# API Settings
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_PER_DAY=1000
API_KEY_EXPIRY_DAYS=365

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://afrola.ai

# Webhook Settings
WEBHOOK_SIGNATURE_HEADER=X-Signature
WEBHOOK_ALLOWED_IPS=127.0.0.1,::1
API Documentation URLs
Once implemented, documentation available at:

Swagger UI: http://localhost:8000/api/docs/

ReDoc: http://localhost:8000/api/redoc/

OpenAPI Schema: http://localhost:8000/api/schema/

Verification Checklist
DRF installed and configured

API routes accessible at /api/

JWT authentication works (login returns token)

API key authentication works (X-API-Key header)

Rate limiting enforced per tier

Pagination works on list endpoints

File upload via API works

Job status endpoint returns progress

Results downloadable in all formats

Dubbing endpoints (voices, previews) work

Webhook registration and delivery works

Error responses formatted correctly

API documentation generated and accessible

CORS configured for frontend domains

API versioning strategy defined (URL prefix /v1/)

All endpoints have OpenAPI annotations

Tests cover all API endpoints

Next Steps After API Implementation
Mobile App Integration - Build Flutter/React Native app using API

Third-party Integrations - Allow partners to use API with rate limits

API Analytics - Track usage per API key in admin dashboard

Rate Limit Dashboard - Monitor API usage and throttling events

API Versioning - Support v2 with breaking changes when needed

SDK Development - Create Python/JavaScript SDKs for easy integration

Related Documentation
docs/user-auth-flow.md - User authentication for API

docs/file-upload-flow.md - File upload API implementation

docs/celery-queue-flow.md - Async job processing via API

docs/subscription-flow.md - Paid API access and rate limits

docs/database-schema.md - API models (APIKey, Webhook)