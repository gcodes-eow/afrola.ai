# backend/dashboard/forms.py

from django import forms
from django.conf import settings
from jobs.models import Job


class MediaUploadForm(forms.Form):
    """Form for uploading media files, text, or YouTube URLs with dubbing options"""

    INPUT_TYPE_CHOICES = [
        ('text', 'Text Input'),
        ('file', 'File Upload'),
        ('youtube', 'YouTube URL'),
    ]

    input_type = forms.ChoiceField(
        choices=INPUT_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='file'
    )
    job_type = forms.ChoiceField(
        choices=Job.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    source_language = forms.ChoiceField(
        choices=[
            ('lg', 'Luganda'),
            ('en', 'English'),
            ('sw', 'Swahili'),
        ],
        initial='lg',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    target_language = forms.ChoiceField(
        choices=[
            ('lg', 'Luganda'),
            ('en', 'English'),
            ('sw', 'Swahili'),
        ],
        initial='en',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    source_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter text to translate...',
        }),
        help_text='Free: 1,000 chars | Pro: 50,000 chars | Enterprise: Unlimited'
    )
    source_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.mp3,.wav,.m4a,.ogg,.flac,.mp4,.avi,.mov,.mkv,.webm'})
    )
    youtube_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.youtube.com/watch?v=...'
        })
    )
    voice_model = forms.ChoiceField(
        choices=[
            ('', 'Default Voice'),
            ('luganda_male_1', 'Luganda Male 1'),
            ('luganda_female_1', 'Luganda Female 1'),
            ('english_male_1', 'English Male 1'),
            ('english_female_1', 'English Female 1'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    add_background_music = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'rounded'})
    )
    background_music_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.mp3,.wav'})
    )
    music_volume = forms.FloatField(
        required=False,
        initial=0.3,
        min_value=0.0,
        max_value=1.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    preserve_timestamps = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'rounded'})
    )
    output_types = forms.MultipleChoiceField(
        choices=Job.OUTPUT_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        initial=['transcript', 'translation']
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        input_type = cleaned_data.get('input_type')
        source_file = cleaned_data.get('source_file')
        youtube_url = cleaned_data.get('youtube_url')
        source_text = cleaned_data.get('source_text')

        if input_type == 'text':
            if not source_text:
                self.add_error('source_text', 'Please enter text to translate.')
            # Auto-set job_type to text_to_text for text input
            cleaned_data['job_type'] = 'text_to_text'
        elif input_type == 'file':
            if not source_file:
                self.add_error('source_file', 'Please select a file to upload.')
        elif input_type == 'youtube':
            if not youtube_url:
                self.add_error('youtube_url', 'Please enter a YouTube URL.')

        return cleaned_data
