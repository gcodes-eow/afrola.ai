docs/file-upload-flow.md

# File Upload Flow — Afrola.ai (Django)

## Purpose
Define how users upload audio/video files and YouTube URLs for translation and dubbing processing, supporting the full media localization pipeline.

## Flow Overview
Upload Form → File Validation → Job Creation → Storage → Queue Task
↓ ↓ ↓ ↓ ↓
User Form Type/Size/ DB Record Media Root Celery
Duration

text

## Architecture Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Upload View | `dashboard/views.py` | Handle file uploads and URL submissions |
| Upload Form | `dashboard/forms.py` | Validate files and dubbing options |
| Job Model | `jobs/models.py` | Track processing state with dubbing fields |
| File Storage | `media/` | Store uploaded files and outputs |
| Validators | `utils/validators.py` | File type/size/duration validation |
| YouTube Downloader | `utils/youtube_downloader.py` | Download YouTube videos |
| FFmpeg Utils | `utils/ffmpeg_utils.py` | Extract duration, audio from video |
| Celery Task | `ai_engine/tasks.py` | Process uploaded files with dubbing |
| Voice Models | `ai/tts/voices/` | Available voices for dubbing |

## Required Files

### Dashboard App (Forms & Views)
backend/dashboard/
├── init.py # ✅
├── forms.py # ⏳ MediaUploadForm, DubbingOptionsForm
├── views.py # ⏳ upload_media view, job_detail view
├── urls.py # ⏳ /upload/, /job/<id>/ routes
├── tests.py # ⏳ Upload tests
└── context_processors.py # ⏳ Dubbing options for templates

text

### Jobs App
backend/jobs/
├── models.py # ✅ Job model (with dubbing fields)
├── admin.py # ✅ Job admin
├── utils.py # ⏳ Job helpers (progress calculation)
└── forms.py # ⏳ Job filtering forms

text

### Utilities
backend/utils/
├── init.py # ✅
├── validators.py # ⏳ File validation functions
├── file_handlers.py # ⏳ File processing utilities
├── ffmpeg_utils.py # ⏳ Media metadata extraction
├── youtube_downloader.py # ⏳ YouTube download with progress
└── subtitle_generator.py # ⏳ SRT/VTT generation

text

### AI Engine
backend/ai_engine/
├── tasks.py # ⏳ process_media_task
├── callbacks.py # ⏳ Post-processing callbacks
└── utils.py # ⏳ Pipeline coordination

text

### Templates
backend/templates/dashboard/
├── upload.html # ⏳ Upload form with dubbing options
├── job_detail.html # ⏳ Job status with preview player
├── audio_preview.html # ⏳ Audio player for preview
├── video_preview.html # ⏳ Video player for preview
├── dubbing_options.html # ⏳ Voice selection form
└── index.html # ⏳ Dashboard with recent jobs

text

## Implementation Plan

### Batch 1: Upload Form with Dubbing Options
**Files to create:**
- `dashboard/forms.py` - MediaUploadForm, DubbingOptionsForm
- `utils/validators.py` - validate_file_type, validate_file_size, validate_youtube_url
- `templates/dashboard/upload.html` - Form with job type selection

**Form Fields:**
| Field | Type | Options |
|-------|------|---------|
| input_type | Choice | File Upload / YouTube URL |
| job_type | Choice | Audio→Text, Video→Text, Audio→Audio, Video→Video, YouTube→Video |
| source_language | Choice | lg, en, sw |
| target_language | Choice | lg, en, sw |
| voice_model | Choice | Male Luganda, Female Luganda, Male English, etc. |
| add_background_music | Boolean | Yes/No |
| generate_subtitles | Boolean | Yes/No |
| file | File | Audio/Video file (conditional) |
| youtube_url | URL | YouTube URL (conditional) |

### Batch 2: File Validation & Metadata Extraction
**Files to create:**
- `utils/ffmpeg_utils.py` - get_media_duration, extract_audio_from_video
- `utils/file_handlers.py` - save_uploaded_file, get_file_size
- `jobs/utils.py` - create_job_record

**Validation Rules:**
| Rule | Value | Error Message |
|------|-------|---------------|
| Max File Size | 500 MB | "File too large. Maximum 500MB" |
| Audio Types | mp3, wav, m4a, ogg, flac | "Unsupported audio format" |
| Video Types | mp4, avi, mov, mkv, webm | "Unsupported video format" |
| Min Duration | 1 second | "File too short" |
| Max Duration (Free) | 600 sec (10 min) | "Upgrade to Pro for longer files" |
| Max Duration (Pro) | 3600 sec (60 min) | "File exceeds Pro limit" |
| YouTube | Valid URL format | "Invalid YouTube URL" |

### Batch 3: Job Creation & Storage
**Files to create:**
- `utils/file_handlers.py` - generate_job_filename, create_job_directory
- `jobs/utils.py` - create_job, update_job_status

**Storage Structure:**
backend/media/
├── uploads/
│ └── YYYY/MM/DD/
│ └── {user_id}/{job_id}_{original_filename}
├── outputs/
│ └── YYYY/MM/DD/
│ └── {user_id}/{job_id}/
│ ├── transcript.txt
│ ├── translation.txt
│ ├── subtitles.srt
│ ├── dubbed_audio.mp3
│ └── dubbed_video.mp4
├── temp/
│ └── {session_id}/{job_id}/
│ ├── downloaded_audio.mp3
│ └── processed_chunks/
└── background_music/
└── default_music.mp3

text

### Batch 4: Celery Task Trigger
**Files to create:**
- `ai_engine/tasks.py` - process_media_task, process_youtube_task
- `ai_engine/callbacks.py` - on_task_success, on_task_failure, on_task_retry

**Task Flow:**
1. Determine job_type from form
2. Create Job record with status='pending'
3. Save file to media/uploads/
4. Trigger appropriate Celery task:
   - `job_type=audio_to_text` → process_audio_to_text_task
   - `job_type=video_to_text` → process_video_to_text_task
   - `job_type=audio_to_audio` → process_audio_dubbing_task
   - `job_type=video_to_video` → process_video_dubbing_task
   - `job_type=youtube_to_video` → process_youtube_dubbing_task
5. Update job status to 'queued'
6. Return job_id to user

### Batch 5: Job Status & Progress Tracking
**Files to create:**
- `dashboard/views.py` - job_detail view, job_status API
- `templates/dashboard/job_detail.html`
- `static/js/job-polling.js`

**Progress Stages:**
Stage | Progress % | Description
------|------------|------------
queued | 5 | Waiting for worker
downloading | 10 | Downloading YouTube video (if applicable)
transcribing | 25 | Converting speech to text
translating | 50 | Translating content
generating_subtitles | 65 | Creating subtitle files
synthesizing_speech | 80 | Generating dubbed audio
merging_audio | 90 | Merging audio/video
completed | 100 | Processing complete

### Batch 6: Results Display & Download
**Files to create:**
- `dashboard/views.py` - download_result view
- `templates/dashboard/audio_preview.html`
- `templates/dashboard/video_preview.html`
- `static/js/audio-player.js`
- `static/js/video-player.js`

**Result Types:**
| Output | Format | Action |
|--------|--------|--------|
| Transcript | TXT/JSON | Download / Copy |
| Translation | TXT/JSON | Download / Copy |
| Subtitles | SRT/VTT | Download / Copy |
| Dubbed Audio | MP3 | Play / Download |
| Dubbed Video | MP4 | Play / Download |

### Batch 7: YouTube Downloader
**Files to create:**
- `utils/youtube_downloader.py` - download_youtube_audio, get_youtube_info
- `ai_engine/tasks.py` - process_youtube_task

**Features:**
- Extract audio only (for faster processing)
- Get video title, duration, thumbnail
- Handle download failures with retry
- Support age-restricted content
- Respect YouTube's terms of service

### Batch 8: Dubbing Options UI
**Files to create:**
- `templates/dashboard/dubbing_options.html`
- `static/js/voice-preview.js`
- `dashboard/views.py` - voice_preview API

**Dubbing Features:**
- Voice selection dropdown with sample preview
- Speed adjustment slider (0.5x - 1.5x)
- Pitch adjustment slider
- Background music selector + volume control
- Output format selection (MP3/MP4)
- Generate preview before final processing

## File Validation Rules

| Rule | Value | Location |
|------|-------|----------|
| Max File Size (Free) | 100 MB | `settings.FREE_MAX_UPLOAD_SIZE_MB` |
| Max File Size (Pro) | 500 MB | `settings.PRO_MAX_UPLOAD_SIZE_MB` |
| Max File Size (Enterprise) | 2000 MB | `settings.ENTERPRISE_MAX_UPLOAD_SIZE_MB` |
| Audio Types | mp3, wav, m4a, ogg, flac | `settings.ALLOWED_AUDIO_TYPES` |
| Video Types | mp4, avi, mov, mkv, webm | `settings.ALLOWED_VIDEO_TYPES` |
| Max Duration (Free) | 600 sec (10 min) | `settings.FREE_MAX_DURATION_SECONDS` |
| Max Duration (Pro) | 3600 sec (60 min) | `settings.PRO_MAX_DURATION_SECONDS` |
| YouTube | Valid URL | `utils/validators.validate_youtube_url` |
| YouTube Duration Limit | 3600 sec | YouTube API check |

## Storage Structure (Detailed)
backend/media/
├── uploads/ # Original user uploads
│ └── {user_id}/
│ └── {YYYY}/{MM}/{DD}/
│ └── {job_id}_{original_name}
│
├── outputs/ # Generated output files
│ └── {user_id}/
│ └── {YYYY}/{MM}/{DD}/
│ └── {job_id}/
│ ├── metadata.json # Job metadata
│ ├── transcript.txt # Plain text transcript
│ ├── translation.txt # Plain text translation
│ ├── transcript.json # Segmented transcript with timestamps
│ ├── subtitles.srt # SubRip subtitle format
│ ├── subtitles.vtt # WebVTT subtitle format
│ ├── dubbed_audio.mp3 # Generated dubbed audio
│ ├── dubbed_audio.wav # High-quality dubbed audio
│ ├── dubbed_video.mp4 # Video with dubbed audio
│ ├── preview_audio.mp3 # 30-second preview for testing
│ └── preview_video.mp4 # 30-second video preview
│
├── temp/ # Temporary processing files
│ └── {session_id}/
│ └── {job_id}/
│ ├── downloaded_audio/ # YouTube audio
│ ├── processed_chunks/ # Segmented audio chunks
│ ├── aligned_segments/ # Forced alignment data
│ └── logs/ # Processing logs
│
└── background_music/ # Background music library
├── default/ # Default music tracks
├── calm/ # Calm/ambient music
├── energetic/ # Upbeat/energetic music
└── custom/ # User-uploaded music

text

## Dependencies

```txt
# requirements.txt additions
ffmpeg-python==0.2.0
pytube==15.0.0
pydub==0.25.1
Pillow==10.1.0
python-magic==0.4.27
Environment Variables
bash
# File Upload Settings
MAX_UPLOAD_SIZE_MB=500
FREE_MAX_UPLOAD_SIZE_MB=100
PRO_MAX_UPLOAD_SIZE_MB=500
ENTERPRISE_MAX_UPLOAD_SIZE_MB=2000

FREE_MAX_DURATION_SECONDS=600
PRO_MAX_DURATION_SECONDS=3600
ENTERPRISE_MAX_DURATION_SECONDS=7200

ALLOWED_AUDIO_TYPES=mp3,wav,m4a,ogg,flac
ALLOWED_VIDEO_TYPES=mp4,avi,mov,mkv,webm

# YouTube Settings
YOUTUBE_API_KEY=your_youtube_api_key
YOUTUBE_DOWNLOAD_TIMEOUT=300
API Endpoints (for AJAX polling)
Method	Endpoint	Description
POST	/api/upload/	Upload file/YouTube URL
GET	/api/jobs/{id}/status/	Get job status & progress
GET	/api/jobs/{id}/results/	Get all output URLs
GET	/api/jobs/{id}/preview/audio/	Get audio preview URL
GET	/api/jobs/{id}/preview/video/	Get video preview URL
POST	/api/jobs/{id}/regenerate/	Regenerate with different voice
GET	/api/voices/	List available voice models
Verification Checklist
Form accepts valid audio/video files

Form accepts valid YouTube URLs

Form rejects invalid file types

Form rejects oversized files (based on tier)

Form rejects over-duration files (based on tier)

YouTube URL validation works

Duration extracted correctly via ffprobe

Job created in database with all fields

File saved to correct media path with user isolation

Celery task triggered with correct parameters

Job status updates through all stages

Progress percentage shows correctly

Results viewable with preview players

Downloads work for all output formats

Dubbing options (voice, music) work

Error handling for failed uploads

AJAX polling updates UI without refresh

YouTube downloads work with progress

Error Handling
Error Scenario	User Message	Action
File too large	"File exceeds size limit. Upgrade to Pro for larger files"	Suggest upgrade
Invalid format	"Unsupported file format. Please use MP3, WAV, MP4, or MOV"	Show allowed types
YouTube unavailable	"Video unavailable or restricted"	Try alternative format
Duration exceeded	"File too long. Free tier limited to 10 minutes"	Show upgrade prompt
Quota exceeded	"Monthly limit reached. Upgrade or wait for reset"	Show usage stats
Processing failed	"Processing failed. Please try again or contact support"	Retry button
Related Documentation
docs/user-auth-flow.md - User authentication for uploads

docs/subscription-flow.md - Tier-based limits

docs/celery-queue-flow.md - Async processing after upload

docs/database-schema.md - Job model fields

docs/api-rest-flow.md - Upload API endpoints