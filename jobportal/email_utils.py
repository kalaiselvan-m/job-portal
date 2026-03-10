from django.core.mail import send_mail
from django.conf import settings


def send_status_email(user_email, subject, message):

    full_message = f"""
Dear Candidate,

{message}

Thank you for using our Job Portal.

Best Regards,
Job Portal Team
"""

    send_mail(
        subject,
        full_message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=True,
    )