docs/training-flow.md

# Training Flow — Afrola.ai (Model Training Pipeline)

## Purpose
Define how custom AI models are trained, fine-tuned, and deployed for improved accuracy in speech recognition, translation, and text-to-speech for African languages.

## Overview
Data Collection → Preprocessing → Training → Evaluation → Deployment → Inference
↓ ↓ ↓ ↓ ↓ ↓
Raw Audio/ Clean/Align Model Metrics Production API
Text Training Validation Server Endpoint

## Architecture Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Training Data | `data/` | Raw and processed datasets |
| Preprocessing Scripts | `training/preprocess.py` | Data cleaning and preparation |
| ASR Training | `training/asr/train_wav2vec.py` | Speech recognition fine-tuning |
| Translation Training | `training/translation/train_nllb.py` | NLLB model fine-tuning |
| TTS Training | `training/tts/train_tts.py` | Coqui TTS voice training |
| Config Files | `training/*/config.yaml` | Hyperparameters and settings |
| Model Registry | `ai/models/` | Stored trained models |
| Evaluation Scripts | `training/evaluate.py` | Model performance metrics |
| Deployment Scripts | `scripts/deploy_model.sh` | Push to production |

## Required Files

### Training Data Organization
data/
├── raw/ # Raw collected data
│ ├── audio/
│ │ ├── luganda/ # Luganda speech recordings
│ │ │ ├── interviews/ # Interview recordings
│ │ │ ├── news/ # News broadcasts
│ │ │ ├── podcasts/ # Podcast episodes
│ │ │ └── youtube/ # YouTube audio extracts
│ │ ├── swahili/ # Swahili speech data
│ │ └── english/ # English speech data
│ ├── video/
│ │ ├── movies/ # Movie clips with subtitles
│ │ ├── lectures/ # Educational content
│ │ └── speeches/ # Public speeches
│ └── text/
│ ├── parallel/ # Parallel text corpora
│ │ ├── luganda_english/ # Luganda-English pairs
│ │ ├── swahili_english/ # Swahili-English pairs
│ │ └── luganda_swahili/ # Luganda-Swahili pairs
│ └── monolingual/ # Single language text
│ ├── luganda/ # Luganda texts
│ ├── swahili/ # Swahili texts
│ └── english/ # English texts
│
├── processed/ # Preprocessed data
│ ├── transcripts/ # Aligned transcripts
│ │ ├── train/ # Training split
│ │ ├── dev/ # Validation split
│ │ └── test/ # Test split
│ ├── features/ # Extracted features
│ │ ├── mfcc/ # MFCC features for ASR
│ │ ├── spectrograms/ # Spectrograms for TTS
│ │ └── embeddings/ # Text embeddings
│ └── parallel_corpus/ # Aligned sentence pairs
│ ├── luganda_english/
│ ├── swahili_english/
│ └── luganda_swahili/
│
└── datasets/ # Ready-to-use datasets
├── luganda_asr/ # HuggingFace format
│ ├── dataset_info.json
│ ├── train-00000.parquet
│ ├── validation-00000.parquet
│ └── test-00000.parquet
├── nllb_luganda_english/ # Translation dataset
└── coqui_luganda_voice/ # TTS voice dataset

### Training Scripts
training/
├── init.py # ✅
├── asr/
│ ├── init.py # ✅
│ ├── train_wav2vec.py # ⏳ Whisper/Wav2Vec2 fine-tuning
│ ├── train_whisper.py # ⏳ Whisper fine-tuning
│ ├── preprocess.py # ⏳ Audio preprocessing
│ ├── evaluate.py # ⏳ ASR evaluation (WER/CER)
│ └── config.yaml # ⏳ ASR hyperparameters
│
├── translation/
│ ├── init.py # ✅
│ ├── train_nllb.py # ⏳ NLLB fine-tuning
│ ├── train_m2m100.py # ⏳ M2M100 fine-tuning
│ ├── preprocess.py # ⏳ Text preprocessing
│ ├── evaluate.py # ⏳ Translation metrics (BLEU/ChrF)
│ └── config.yaml # ⏳ Translation hyperparameters
│
├── tts/
│ ├── init.py # ✅
│ ├── train_tts.py # ⏳ Coqui TTS training
│ ├── train_vits.py # ⏳ VITS fine-tuning
│ ├── preprocess.py # ⏳ Audio-text alignment
│ ├── evaluate.py # ⏳ TTS evaluation (MOS)
│ ├── voice_cloning.py # ⏳ Voice cloning training
│ └── config.yaml # ⏳ TTS hyperparameters
│
├── shared/
│ ├── init.py # ✅
│ ├── metrics.py # ⏳ Common evaluation metrics
│ ├── utils.py # ⏳ Shared utilities
│ └── model_registry.py # ⏳ Model version tracking
│
├── evaluate.py # ⏳ Master evaluation script
├── export.py # ⏳ Export to production format
└── monitor.py # ⏳ Training monitoring

### Configuration Files
training/asr/config.yaml # ⏳ ASR training config
training/translation/config.yaml # ⏳ Translation training config
training/tts/config.yaml # ⏳ TTS training config

### Model Registry
ai/models/
├── asr/ # ASR models
│ ├── whisper_luganda_base/ # Base fine-tuned model
│ ├── whisper_luganda_large/ # Large fine-tuned model
│ └── wav2vec2_luganda/ # Wav2Vec2 model
├── translation/ # Translation models
│ ├── nllb_luganda_english/ # NLLB fine-tuned
│ ├── nllb_swahili_english/ # Swahili-English model
│ └── m2m100_luganda_swahili/ # Luganda-Swahili model
└── tts/ # TTS models
├── coqui_luganda_female/ # Female voice model
├── coqui_luganda_male/ # Male voice model
└── coqui_swahili_female/ # Swahili voice model

## Implementation Plan

### Batch 1: Data Collection Pipeline

**Files to create:**
- `scripts/download_youtube.py` - Scrape YouTube for content
- `scripts/scrape_news.py` - Collect news broadcasts
- `scripts/extract_subtitles.py` - Extract subtitles from videos
- `scripts/clean_text.py` - Text cleaning utilities

**Data Sources:**
| Source | Type | Languages | Volume Target |
|--------|------|-----------|---------------|
| YouTube | Audio/Video | Luganda, English, Swahili | 1000 hours |
| News Broadcasts | Audio | All | 500 hours |
| Public Domain Books | Text | English, Swahili | 10M sentences |
| Social Media | Text | Luganda, Swahili | 5M sentences |
| Bible Translations | Parallel Text | All | 31K verses |
| OpenSubtitles | Parallel Subtitles | All | 10M lines |

### Batch 2: Data Preprocessing

**Files to create:**
- `training/asr/preprocess.py` - Audio preprocessing
- `training/translation/preprocess.py` - Text preprocessing
- `training/tts/preprocess.py` - TTS data preparation
- `training/shared/utils.py` - Shared utilities

**ASR Preprocessing:**

# training/asr/config.yaml
audio:
  sample_rate: 16000
  min_duration: 0.5
  max_duration: 30.0
  noise_augmentation: true
  speed_augmentation: [0.9, 1.0, 1.1]
  
text:
  normalization: true
  lowercase: true
  remove_punctuation: false
  
dataset:
  train_split: 0.8
  dev_split: 0.1
  test_split: 0.1

Batch 3: ASR Model Training (Whisper/Wav2Vec2)
Files to create:

training/asr/train_whisper.py - Whisper fine-tuning

training/asr/train_wav2vec.py - Wav2Vec2 fine-tuning

training/asr/evaluate.py - WER/CER calculation

Training Configuration:

# training/asr/config.yaml
model:
  name: whisper-small
  pretrained: openai/whisper-small
  language: luganda
  
training:
  batch_size: 16
  learning_rate: 1e-5
  epochs: 10
  gradient_accumulation_steps: 4
  fp16: true
  
evaluation:
  metrics: [wer, cer]
  save_best: true

Batch 4: Translation Model Training (NLLB)
Files to create:

training/translation/train_nllb.py - NLLB fine-tuning

training/translation/train_m2m100.py - M2M100 fine-tuning

training/translation/evaluate.py - BLEU/ChrF calculation

Training Configuration:

# training/translation/config.yaml
model:
  name: nllb-200-distilled
  pretrained: facebook/nllb-200-distilled-600M
  source_lang: lug_Latn
  target_lang: eng_Latn
  
training:
  batch_size: 32
  learning_rate: 3e-5
  epochs: 5
  warmup_steps: 500
  
evaluation:
  metrics: [bleu, chrf, ter]
  max_length: 128
Batch 5: TTS Model Training (Coqui TTS)
Files to create:

training/tts/train_tts.py - Coqui TTS training

training/tts/train_vits.py - VITS fine-tuning

training/tts/voice_cloning.py - Voice cloning

training/tts/evaluate.py - MOS evaluation

Training Configuration:

# training/tts/config.yaml
model:
  name: coqui-tts
  architecture: vits
  num_speakers: 2
  
training:
  batch_size: 32
  learning_rate: 1e-4
  epochs: 1000
  save_step: 10000
  
audio:
  sample_rate: 22050
  hop_length: 256
  win_length: 1024
  n_mels: 80
  
voice:
  speakers:
    - name: luganda_female
      samples: 5000
    - name: luganda_male
      samples: 5000

Batch 6: Model Evaluation & Selection
Files to create:

training/evaluate.py - Master evaluation script

training/shared/metrics.py - Common metrics

training/leaderboard.py - Model comparison

Evaluation Metrics:

Model Type	Primary Metric	Secondary Metrics
ASR	WER (Word Error Rate)	CER, RTF, Accuracy
Translation	BLEU	ChrF, TER, COMET
TTS	MOS (Mean Opinion Score)	MCD, F0 RMSE

Batch 7: Model Export & Quantization
Files to create:

training/export.py - Export to production format

training/quantize.py - Model quantization

scripts/optimize_model.sh - Optimization script

Export Formats:

Format	Use Case	Size Reduction
PyTorch (.pt)	Development	None
ONNX	Inference	30-50%
TensorRT	GPU Inference	50-70%
CoreML	iOS	40-60%
TensorFlow Lite	Android/Edge	60-80%

Batch 8: Model Registry & Versioning
Files to create:

training/shared/model_registry.py - Version tracking

ai_engine/models.py - Database model registry

scripts/deploy_model.sh - Deployment script

Model Version Schema:

text
{model_type}/{language_task}/{version}_{timestamp}

Examples:
asr/luganda/v1.0_20250115
translation/luganda_english/v2.1_20250201
tts/luganda_female/v1.2_20250130

Batch 9: Continuous Training Pipeline
Files to create:

scripts/data_versioning.py - Data version control

scripts/trigger_training.py - Auto-trigger training

infra/docker/Dockerfile.training - Training container

CI/CD Pipeline:

# .github/workflows/training.yml
name: Model Training
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:  # Manual trigger

jobs:
  train:
    runs-on: gpu-runner
    steps:
      - checkout
      - run: python training/asr/train_whisper.py
      - run: python training/evaluate.py
      - run: python training/export.py
      - run: python scripts/deploy_model.py

Batch 10: Production Integration
Files to create:

ai_engine/model_loader.py - Dynamic model loading

ai_engine/model_cache.py - Model caching

config/settings.py - Model configuration

Production Settings:

# Model configuration
MODEL_CONFIG = {
    'asr': {
        'model_path': 'ai/models/asr/whisper_luganda_large',
        'device': 'cuda',
        'batch_size': 32,
    },
    'translation': {
        'model_path': 'ai/models/translation/nllb_luganda_english',
        'beam_size': 5,
        'max_length': 512,
    },
    'tts': {
        'model_path': 'ai/models/tts/coqui_luganda_female',
        'sample_rate': 22050,
    }
}

Data Collection Strategy

Phase 1: Luganda (Launch)
Source	Hours/Sentences	Collection Method
YouTube sermons, music	500 hours	YouTube API
Radio broadcasts	200 hours	API/Recording
Parliamentary speeches	100 hours	Public archives
Bible (parallel text)	31K sentences	Public domain
News articles	100K sentences	Web scraping

Phase 2: Swahili (Q2 2025)
Source	Hours/Sentences	Collection Method
YouTube content	1000 hours	YouTube API
Swahili literature	1M sentences	Public domain books
News websites	500K sentences	Web scraping
Social media	1M sentences	Twitter API

Phase 3: Additional Languages (Q3 2025)
Amharic
Yoruba
Hausa

Hardware Requirements
Training Type	GPU	RAM	Storage	Time
ASR (Whisper small)	24GB (RTX 3090)	32GB	100GB	2-3 days
ASR (Whisper large)	48GB (A6000)	64GB	200GB	7-10 days
Translation (NLLB 600M)	24GB (RTX 3090)	32GB	50GB	3-5 days
TTS (Coqui)	24GB (RTX 3090)	32GB	100GB	5-7 days
Evaluation Criteria

ASR Model (WER target: <15%)
Metric	Baseline	Target	Stretch
WER (clean speech)	25%	15%	10%
WER (noisy speech)	40%	25%	20%
RTF (Real Time Factor)	0.5	0.2	0.1

Translation Model (BLEU target: >30)
Metric	Baseline	Target	Stretch
BLEU (Luganda→English)	15	30	40
BLEU (English→Luganda)	12	25	35
COMET Score	0.5	0.7	0.8

TTS Model (MOS target: >4.0)
Metric	Baseline	Target	Stretch
MOS (Naturalness)	3.0	4.0	4.5
MCD (Mel Cepstral Distortion)	8	5	3
Speaker Similarity	N/A	0.8	0.9
Dependencies
txt

# training/requirements.txt
torch==2.1.0
torchaudio==2.1.0
transformers==4.36.0
datasets==2.15.0
accelerate==0.25.0
wandb==0.16.0

# ASR
openai-whisper==20231117
librosa==0.10.0
soundfile==0.12.1

# Translation
sentencepiece==0.1.99
sacremoses==0.0.53

# TTS
TTS==0.20.0
coqui-tts==0.20.0

# Evaluation
jiwer==3.0.0
evaluate==0.4.0
nltk==3.8.1
Environment Variables
bash
# Training
MODEL_CACHE_DIR=/models
DATA_DIR=/data
OUTPUT_DIR=/outputs

# WandB (logging)
WANDB_API_KEY=your_wandb_api_key
WANDB_PROJECT=afrola-training

# HuggingFace
HF_TOKEN=your_hf_token

# Compute
CUDA_VISIBLE_DEVICES=0,1
OMP_NUM_THREADS=8
Verification Checklist
Data collected from all sources

Data preprocessing scripts working

Training configs configured correctly

ASR model training runs without errors

Translation model training runs

TTS model training runs

Evaluation metrics calculated

Best model checkpoints saved

Model exported to production format

Model registry updated

Production integration working

Continuous training pipeline set up

Related Documentation
docs/database-schema.md - Model registry tables

docs/api-rest-flow.md - Model endpoints

docs/celery-queue-flow.md - Async training jobs

docs/file-upload-flow.md - Dataset upload