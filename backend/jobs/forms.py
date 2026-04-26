# backend/jobs/forms.py

from django import forms
from .models import Job


class JobFilterForm(forms.Form):
    """Form for filtering jobs on the dashboard"""
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Job.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg',
            'onchange': 'this.form.submit()'
        })
    )
    job_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Job.TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg',
            'onchange': 'this.form.submit()'
        })
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg',
            'placeholder': 'Search jobs...'
        })
    )
