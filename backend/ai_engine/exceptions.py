# backend/ai_engine/exceptions.py

"""Custom exceptions for AI engine tasks."""

class AITaskError(Exception):
    """Base exception for AI processing tasks."""
    pass


class TranscriptionError(AITaskError):
    """Error during transcription/speech recognition."""
    pass


class TranslationError(AITaskError):
    """Error during text translation."""
    pass


class TTSynthesisError(AITaskError):
    """Error during text-to-speech synthesis."""
    pass


class SubtitleGenerationError(AITaskError):
    """Error during subtitle file generation."""
    pass


class YouTubeDownloadError(AITaskError):
    """Error downloading YouTube videos."""
    pass


class AudioExtractionError(AITaskError):
    """Error extracting audio from video."""
    pass


class ModelNotAvailableError(AITaskError):
    """Requested AI model is not available."""
    pass


class QuotaExceededError(AITaskError):
    """User has exceeded their processing quota."""
    pass


class FileValidationError(AITaskError):
    """Uploaded file fails validation."""
    pass
