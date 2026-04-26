# backend/accounts/utils.py

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_verification_email(user, request):
    """Generate verification token and send email"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    user.email_verification_token = token
    user.save(update_fields=['email_verification_token'])

    verification_url = f"{settings.FRONTEND_URL}/verify/{uid}/{token}/"

    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': settings.SITE_NAME,
    }

    html_message = render_to_string('accounts/verification_email.html', context)
    plain_message = (
        f"Hi {user.full_name},\n\n"
        f"Please verify your email by clicking the link below:\n"
        f"{verification_url}\n\n"
        f"If you did not create an account, please ignore this email.\n\n"
        f"Thanks,\n{settings.SITE_NAME} Team"
    )

    send_mail(
        subject=f'Verify your email - {settings.SITE_NAME}',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )