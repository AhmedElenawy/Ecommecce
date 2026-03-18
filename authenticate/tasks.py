from celery import shared_task
from ecommerce.redis_client import r
# from django.core.mail import send_mail
from django.core.mail import EmailMessage, EmailMultiAlternatives
from smtplib import SMTPException

# resend when raise on following errors 
# it retry 3 times after 60 seconds
# retry_backoff means first 1 min, then 2 min, then 4 min
@shared_task(bind=True,
    autoretry_for=(SMTPException, ConnectionError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True)
def send_email(self,otp, purpose, recipient_email):


    if not recipient_email or not otp or not purpose:
        raise ValueError("Email, OTP, and purpose must be provided.")
    

    subject = "Your OTP for " + purpose
    text_body = f"Your OTP for {purpose} is: {otp}"
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
            <h2 style="color: #333;">Verification Code</h2>
            <p>Your OTP for <strong>{purpose}</strong> is:</p>
            <h1 style="color: #007bff; letter-spacing: 5px; font-size: 32px;">{otp}</h1>
            <p style="color: #666;">This code is required to complete your request. If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """
    try:
        email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=None,
        to=[recipient_email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
    except Exception as e:
        raise
    