from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
import random


# =========================
# CUSTOM USER MODEL
# =========================

class User(AbstractUser):

    ROLE_CHOICES = (
        ('seeker', 'Job Seeker'),
        ('employer', 'Employer'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Contact info
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)

    # Employer field
    company_name = models.CharField(max_length=200, blank=True, null=True)

    # Job seeker fields
    skills = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    resume = models.FileField(
        upload_to='resumes/',
        blank=True,
        null=True
    )

    # Email verification
    is_verified = models.BooleanField(default=False)

    # OTP system
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    # =========================
    # OTP FUNCTIONS
    # =========================

    def generate_otp(self):
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.save()

    def verify_otp(self, otp_input):

        if self.otp_code != otp_input:
            return False

        if self.otp_created_at:
            expiry_time = self.otp_created_at + timezone.timedelta(minutes=5)

            if timezone.now() > expiry_time:
                return False

        self.is_verified = True
        self.is_active = True
        self.otp_code = None
        self.save()

        return True

    # =========================
    # MODEL VALIDATION
    # =========================

    def clean(self):

        if self.role == 'employer' and not self.company_name:
            raise ValidationError("Company name is required for employers.")

        if self.role == 'seeker' and not self.resume:
            raise ValidationError("Resume is required for job seekers.")

    def __str__(self):
        return self.username


# =========================
# JOB MODEL
# =========================

class Job(models.Model):

    employer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'employer'},
        related_name='posted_jobs'
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    skills_required = models.TextField(
        help_text="Example: Python:3, Django:2, SQL:1"
    )

    location = models.CharField(max_length=200)

    minimum_ats_score = models.FloatField(
        default=60,
        help_text="Minimum ATS score required"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('title', 'location', 'employer')
        ordering = ['-created_at']

    def __str__(self):
        company = self.employer.company_name or self.employer.username
        return f"{self.title} - {company}"


# =========================
# APPLICATION MODEL
# =========================

class Application(models.Model):

    STATUS_CHOICES = (
        ('Applied', 'Applied'),
        ('Under Review', 'Under Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected'),
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_applications",
        limit_choices_to={'role': 'seeker'}
    )

    resume = models.FileField(
    upload_to='resumes/',
    blank=True,
    null=True
)

    ats_score = models.FloatField(default=0)

    matched_skills = models.TextField(blank=True)
    missing_skills = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Applied'
    )

    rejection_reason = models.TextField(blank=True)

    # HR manual override
    is_override = models.BooleanField(default=False)

    # Reconsider system
    reconsider_requested = models.BooleanField(default=False)
    reconsider_count = models.IntegerField(default=0)

    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('job', 'applicant')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} → {self.job.title}"


# =========================
# AUDIT LOG SYSTEM
# =========================

class AuditLog(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    action = models.CharField(max_length=255)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"