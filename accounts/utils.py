from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

def send_waiting_approval_email(user):
    subject = "Registration Received – Awaiting Admin Approval"
    message = f"""
Dear {user.first_name or user.username},

Thank you for registering with the Department of CSE, BRUR.

Your account has been created successfully, but it is currently **pending admin approval** 
and document verification.

You will receive another email once your account is approved. Until then, you will not 
be able to log in.

Thank you for your patience.

Best regards,
Department of Computer Science & Engineering
Begum Rokeya University, Rangpur
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    
def send_account_approval_email(user, is_approved=True, remarks=None):
    subject = f"Your Account has been {'Approved' if is_approved else 'Rejected/Unapproved'}"

    if is_approved:
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #4f46e5;">Account Approved!</h2>
            <p>Dear <strong>{user.first_name or user.username}</strong>,</p>
            <p>Your account has been <strong>approved</strong> by the admin.</p>
            <p>You can now <a href="http://yourdomain.com/login" style="color: #4f46e5;">log in</a> and use all features.</p>
            <p>Thank you for joining us!</p>
            <p>Best regards,<br>
            <strong>Department of Computer Science & Engineering</strong><br>
            Begum Rokeya University, Rangpur</p>
        </body>
        </html>
        """
    else:
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #ef4444;">Account Status Update</h2>
            <p>Dear <strong>{user.first_name or user.username}</strong>,</p>
            <p>Your account approval has been <strong>revoked</strong> or <strong>rejected</strong>.</p>
            {f'<p><strong>Reason/Remarks:</strong> {remarks}</p>' if remarks else ''}
            <p>Please contact support if you have questions.</p>
            <p>Best regards,<br>
            <strong>Department of Computer Science & Engineering</strong><br>
            Begum Rokeya University, Rangpur</p>
        </body>
        </html>
        """

    send_mail(
        subject=subject,
        message="Plain text fallback",
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

def send_verification_approval_email(verification, is_verified=True, remarks=None):
    """
    Send email when admin approves or rejects a verification document.
    """
    user = verification.user
    doc_type = verification.get_verification_type_display()

    subject = f"Your {doc_type} Verification has been { 'Approved' if is_verified else 'Rejected' }"

    if is_verified:
        message = (
            f"Dear {user.first_name or user.username},\n\n"
            f"Your uploaded {doc_type} has been verified and approved.\n"
            f"Your account is now fully active.\n\n"
            f"Thank you,\n"
            f"{settings.SITE_NAME or 'Your Platform'} Team"
        )
    else:
        message = (
            f"Dear {user.first_name or user.username},\n\n"
            f"Your uploaded {doc_type} was reviewed but not approved.\n"
        )
        if remarks:
            message += f"Reason/Remarks: {remarks}\n\n"
        message += (
            f"Please upload a clearer/correct document or contact support.\n\n"
            f"Regards,\n"
            f"{settings.SITE_NAME or 'Your Platform'} Team"
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    
    
def send_result_notification(user, semester, sgpa, cgpa, status):
    """
    Send email & in-app notification when semester result is published.
    """
    subject = f"Result Published: {semester} - SGPA {sgpa}"

    message = f"""
Dear {user.first_name or user.username},

Your result for **{semester}** has been published.

SGPA: {sgpa}
CGPA: {cgpa}
Status: {status.capitalize()}

You can view full details and previous semesters in your profile dashboard.

Best regards,
Department of Computer Science & Engineering
Begum Rokeya University, Rangpur
    """

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(f"Email sent to {user.email} for {semester}")
    except Exception as e:
        print(f"Email failed for {user.email}: {e}")

    # Optional: create in-app notification (if you have Notification model later)
    # Notification.objects.create(
    #     user=user,
    #     title=subject,
    #     message=message,
    #     notification_type='result'
    # )