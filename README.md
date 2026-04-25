# afrola/Architecture.md

Afrola — Django-Only Architecture

Project Goal
Afrola.ai is an AI-powered web platform designed to automatically translate audio and video content between languages, starting with Luganda and English. The goal is to make spoken content universally accessible by converting speech into accurate text, translating it, and optionally generating subtitles or dubbed audio in the target language.

The platform will enable users to upload media files or provide YouTube links, after which afrola.ai will process the content through a structured AI pipeline. This includes speech recognition, translation, subtitle generation, and optional voice synthesis. The system is built to handle multiple file formats and deliver outputs such as transcripts, translated text, subtitle files (SRT/VTT), and audio translations.

Afrola.ai is designed with scalability in mind, using a pure Django architecture with integrated Celery for async processing. It will leverage existing machine learning models initially, with plans to improve accuracy through custom training on Luganda datasets. Over time, the platform will expand to support more African languages and dialects.

The broader objective is to bridge language barriers in digital media, enabling content creators, educators, media houses, and everyday users to reach wider audiences. By focusing first on underserved languages, afrola.ai aims to become a leading solution for multilingual media accessibility in emerging markets.

Ultimately, afrola.ai seeks to transform how people consume and share spoken content across languages, making information more inclusive, accessible, and globally connected.

AFROLA/
├── docs/                                 # Documentation
│   ├── api-rest-flow.md
│   ├── celery-queue-flow.md
│   ├── database-schema.md
│   ├── file-upload-flow.md
│   ├── subscription-flow.md
│   ├── tranining-flow.md
│   └── user-auth-flow.md
│
├── ai/                                   # Core AI logic (Python)
│   ├── asr/
│   │   ├── whisper_model.py
│   │   ├── inference.py
│   │   └── fine_tune/
│   │       ├── train.py
│   │       └── config.yaml
│   │
│   ├── translation/
│   │   ├── nllb_model.py
│   │   ├── translate.py
│   │   └── fine_tune/
│   │       ├── train.py
│   │       └── config.yaml
│   │
│   ├── tts/
│   │   ├── coqui_model.py
│   │   ├── synthesize.py
│   │   └── voices/
│   │       ├── swahili/ # And others (future)
│   │       └── luganda/
│   │
│   ├── alignment/
│   │   ├── aligner.py
│   │   └── forced_alignment.py
│   │
│   └── pipelines/
│       ├── audio_pipeline.py
│       ├── video_pipeline.py
│       └── youtube_pipeline.py
│
├── backend/                              # Django project root
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── settings_production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   │
│   ├── accounts/                        # User management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── decorators.py
│   │   ├── signals.py
│   │   ├── tests.py
│   │   └── utils.py
│   │
│   ├── jobs/                # Job management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── tests.py
│   │   └── utils.py
│   │
│   ├── ai_engine/           # AI integration
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tasks.py
│   │   ├── callbacks.py
│   │   ├── tests.py
│   │   ├── utils.py
│   │   └── views.py
│   │
│   ├── pricing/                         # Subscription plans
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── stripe_utils.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── utils.py
│   │   └── webhooks.py
│   │
│   ├── payments/                        # Payment processing
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── tests.py
│   │   ├── webhooks.py
│   │   └── stripe_utils.py
│   │
│   ├── dashboard/                   # User dashboard views
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── context_processors.py
│   │   ├── tests.py
│   │   └── views.py
│   │
│   ├── api/                            # REST API (for future mobile apps)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── tests.py
│   │   └── views.py
│   │
│   ├── templates/                       # Django HTML templates
│   │   ├── base.html
│   │   ├── 404.html
│   │   ├── 500.html
│   │   │
│   │   ├── accounts/
│   │   │   ├── login.html
│   │   │   ├── password_reset_confirm.html
│   │   │   ├── password_reset_done.html
│   │   │   ├── password_reset_email.html
│   │   │   ├── password_reset_form.html
│   │   │   ├── profile.html
│   │   │   └── register.html
│   │   │
│   │   ├── dashboard/
│   │   │   ├── index.html
│   │   │   ├── audio_preview.html
│   │   │   ├── video_preview.html
│   │   │   ├── dubbing_options.html
│   │   │   ├── upload.html
│   │   │   ├── job_detail.html
│   │   │   └── settings.html
│   │   │
│   │   ├── pricing/
│   │   │   ├── index.html
│   │   │   └── checkout.html
│   │   │
│   │   └── includes/
│   │       ├── navbar.html
│   │       ├── footer.html
│   │       └── messages.html
│   │
│   ├── static/                          # Static files (CSS, JS, images)
│   │   ├── css/
│   │   │   ├── tailwind.css
│   │   │   ├── main.css
│   │   │   └── components.css
│   │   │
│   │   ├── js/
│   │   │   ├── dashboard.js
│   │   │   ├── file-upload.js
│   │   │   ├── job-polling.js
│   │   │   └── utils.js
│   │   │
│   │   └── images/
│   │       ├── logo.png
│   │       └── favicon.ico
│   │
│   ├── media/                     # User uploaded files (gitignored)
│   │   ├── uploads/
│   │   ├── subtitles/
│   │   ├── audio/
│   │   └── temp/
│   │
│   ├── staticfiles/                     # Collected static files
│   ├── logs/                            # Application logs (gitignored)
│   ├── fixtures/                        # Initial data fixtures
│   │   ├── initial_data.json
│   │   └── test_data.json
│   │
│   └── utils/                           # Utility scripts
│       ├── __init__.py
│       ├── ffmpeg_utils.py
│       ├── file_handlers.py
│       ├── mobile_money.py
│       ├── subtitle_generator.py
│       ├── validators.py
│       └── youtube_downloader.py
│   │
│   └── venv/           # Virtual environment
│
├── data/                                # Training data (Phase 3)
│   ├── raw/
│   │   ├── audio/
│   │   ├── video/
│   │   └── text/
│   │
│   ├── processed/
│   │   ├── transcripts/
│   │   └── parallel_corpus/
│   │
│   └── datasets/
│       ├── luganda_en/
│       └── evaluation/
│
├── training/                            # Model training scripts
│   ├── asr/
│   │   ├── train_wav2vec.py
│   │   ├── preprocess.py
│   │   └── config.yaml
│   │
│   ├── translation/
│   │   ├── train_nllb.py
│   │   ├── preprocess.py
│   │   └── config.yaml
│   │
│   └── tts/
│       ├── train_tts.py
│       ├── preprocess.py
│       └── config.yaml
│
├── scripts/                            # Utility scripts
│   ├── download_youtube.py
│   ├── preprocess_audio.py
│   ├── generate_subtitles.py
│   ├── backup_db.sh
│   └── deploy.sh
│
├── infra/                              # Infrastructure
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.celery
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.prod.yml
│   │   └── .env.docker
│   │
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── sites-available/
│   │       └── afrola.conf
│   │
│   └── gunicorn/
│       └── gunicorn.conf.py
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── test_accounts.py
│   ├── test_jobs.py
│   ├── test_ai_engine.py
│   ├── test_pipelines.py
│   ├── test_api.py
│   └── conftest.py
│
├── .env                                # Environment variables
├── .env.example                        # Example environment file
├── .gitignore
├── .dockerignore
├── README.md
├── LICENSE
├── docker-compose.yml
├── Dockerfile
├── Makefile                            # Common commands
└── pyproject.toml                      # Python project config

# IMPLEMENTATION WORKFLOW DOCUMENTATION (UPDATED)

## Phase 1: Foundation (Week 1)
1. docs/database-schema.md           # Create all models first
2. docs/user-auth-flow.md            # Authentication on top of models

## Phase 2: Core Features (Week 2-3)
3. docs/file-upload-flow.md          # Basic upload without async (synchronous first)
   └── Implement Celery LATER (move queue logic to Phase 3)

4. docs/subscription-flow.md         # Payment integration (Stripe webhooks)
   └── Can work independently after auth

## Phase 3: Async Processing (Week 4)
5. docs/celery-queue-flow.md         # Add async AFTER upload works synchronously
   └── Refactor upload to use Celery

## Phase 4: API & Integration (Week 5-6)
6. docs/api-rest-flow.md             # API endpoints after all features work

## Phase 5: ML/AI Improvement (Parallel - Week 3+)
7. docs/training-flow.md             # Can run parallel to other phases
