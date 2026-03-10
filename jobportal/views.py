from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Avg
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import random
import PyPDF2
import json
import threading

# Local imports
from .models import Job, Application, AuditLog, User
from .forms import RegisterForm, JobForm
from .utils import calculate_ats_score
from .email_utils import send_status_email
from .decorators import role_required
from .services import sort_applications_highest


# ======================================
# HOME
# ======================================

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'landing.html')

    jobs = Job.objects.all()
    return render(request, 'home.html', {'jobs': jobs})

# ======================================
# SEND OTP (AJAX)
# ======================================


def send_otp(request):

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"})

    try:
        data = json.loads(request.body)
        email = data.get("email")
    except:
        email = request.POST.get("email")

    if not email:
        return JsonResponse({
            "status": "error",
            "message": "Email is required"
        })

    otp = str(random.randint(100000, 999999))

    # store session data
    request.session["otp_code"] = otp
    request.session["otp_email"] = email
    request.session["otp_verified"] = False
    request.session["otp_time"] = timezone.now().timestamp()

    # send email in background
    def send_mail_background():
        send_status_email(
            email,
            "Your Verification Code",
            f"Your OTP verification code is: {otp}"
        )

    threading.Thread(target=send_mail_background).start()

    return JsonResponse({
        "status": "success",
        "message": "OTP sent successfully"
    })
# ======================================
# REGISTER (CLEAN FINAL VERSION)
# ======================================


def register_view(request):

    form = RegisterForm(request.POST or None, request.FILES or None)

    if request.method == "POST":

        if not request.session.get("otp_verified"):
            messages.error(request, "Please verify your email first.")
            return render(request, "register.html", {"form": form})

        if form.is_valid():

            user = form.save(commit=False)

            user.role = form.cleaned_data.get("role")
            user.phone = form.cleaned_data.get("phone")
            user.company_name = form.cleaned_data.get("company_name")
            user.resume = form.cleaned_data.get("resume")

            user.is_active = True
            user.is_verified = True

            user.save()

            # clear session
            request.session.pop("otp_verified", None)
            request.session.pop("otp_code", None)
            request.session.pop("otp_email", None)
            request.session.pop("otp_time", None)

            messages.success(request, "Account created successfully. Please login.")

            return redirect("login")

        messages.error(request, "Please correct the errors below.")

    return render(request, "register.html", {"form": form})
# ======================================
# VERIFY OTP
# ======================================


def verify_otp(request):

    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Invalid request"
        })

    try:
        data = json.loads(request.body)
        email = data.get("email")
        otp_entered = data.get("otp")
    except:
        email = request.POST.get("email")
        otp_entered = request.POST.get("otp")

    session_email = request.session.get("otp_email")
    session_otp = request.session.get("otp_code")
    otp_time = request.session.get("otp_time")

    # email validation
    if not session_email or email != session_email:
        return JsonResponse({
            "status": "error",
            "message": "Email mismatch"
        })

    # OTP expiration (5 minutes)
    if otp_time:
        current_time = timezone.now().timestamp()

        if current_time - otp_time > 300:
            request.session.pop("otp_code", None)
            return JsonResponse({
                "status": "error",
                "message": "OTP expired. Please request a new one."
            })

    # OTP validation
    if str(otp_entered).strip() == str(session_otp).strip():

        request.session["otp_verified"] = True

        request.session.pop("otp_code", None)
        request.session.pop("otp_email", None)
        request.session.pop("otp_time", None)

        return JsonResponse({
            "status": "success",
            "message": "OTP verified successfully"
        })

    return JsonResponse({
        "status": "error",
        "message": "Invalid OTP"
    })
# ======================================
# LOGIN
# ======================================

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if form.is_valid():
        user = form.get_user()

        if not user.is_verified:
            messages.error(request, "Please verify your email first.")
            return redirect('login')

        login(request, user)

        AuditLog.objects.create(
            user=user,
            action="Logged into system"
        )

        return redirect('home')

    return render(request, 'login.html', {'form': form})


# ======================================
# LOGOUT
# ======================================

def logout_view(request):
    logout(request)
    return redirect('home')


# ======================================
# POST JOB
# ======================================

@login_required
@role_required('employer')
def post_job(request):

    if not request.user.is_verified:
        messages.error(request, "Please verify your email before posting jobs.")
        return redirect('home')

    form = JobForm(request.POST or None)

    if form.is_valid():
        job = form.save(commit=False)
        job.employer = request.user
        job.save()

        AuditLog.objects.create(
            user=request.user,
            action=f"Posted job: {job.title}"
        )

        messages.success(request, "Job posted successfully.")
        return redirect('employer_dashboard')

    return render(request, 'post_job.html', {'form': form})
# ======================================
# APPLY JOB (HYBRID NLP ATS SYSTEM)
# ======================================

@login_required
@role_required('seeker')
def apply_job(request, job_id):

    job = get_object_or_404(Job, id=job_id)

    # -----------------------------------
    # PREPARE SKILLS FOR TEMPLATE
    # -----------------------------------
    skills_list = []
    if job.skills_required:
        skills_list = [s.strip() for s in job.skills_required.split(",")]

    # -----------------------------------
    # SHOW JOB DETAILS PAGE
    # -----------------------------------
    if request.method == "GET":

        return render(
            request,
            "apply_job.html",
            {
                "job": job,
                "skills_list": skills_list
            }
        )

    # -----------------------------------
    # PREVENT DUPLICATE APPLICATION
    # -----------------------------------
    if Application.objects.filter(job=job, applicant=request.user).exists():

        messages.warning(request, "You already applied for this job.")
        return redirect("seeker_dashboard")

    resume = request.user.resume

    # -----------------------------------
    # CHECK RESUME
    # -----------------------------------
    if not resume:

        messages.error(request, "Please upload your resume before applying.")
        return redirect("seeker_dashboard")

    resume_text = ""

    # -----------------------------------
    # READ PDF RESUME SAFELY
    # -----------------------------------
    try:

        pdf_reader = PyPDF2.PdfReader(resume)

        for page in pdf_reader.pages:

            text = page.extract_text()

            if text:
                resume_text += text + " "

    except Exception:

        messages.error(request, "Unable to read resume file.")
        return redirect("seeker_dashboard")

    # -----------------------------------
    # CALCULATE ATS SCORE
    # -----------------------------------
    score, matched, missing = calculate_ats_score(
        resume_text,
        job.skills_required
    )

    # -----------------------------------
    # DETERMINE STATUS
    # -----------------------------------
    if score >= job.minimum_ats_score:

        status = "Shortlisted"
        reason = ""

        messages.success(
            request,
            f"Application submitted successfully! ATS Score: {score}%"
        )

    else:

        status = "Rejected"

        missing_display = ", ".join(missing[:5]) if missing else "Insufficient skill match"

        reason = (
            "Your resume did not meet the required selection criteria.\n\n"
            f"ATS Score: {score}%\n\n"
            f"Missing Skills: {missing_display}"
        )

        # SEND EMAIL
        try:
            send_status_email(
                request.user.email,
                "Application Rejected",
                reason
            )
        except:
            pass

        messages.error(
            request,
            f"Application rejected automatically. ATS Score: {score}%"
        )

    # -----------------------------------
    # SAVE APPLICATION
    # -----------------------------------
    Application.objects.create(

        job=job,
        applicant=request.user,
        ats_score=score,
        matched_skills=", ".join(matched),
        missing_skills=", ".join(missing),
        status=status,
        rejection_reason=reason

    )

    # -----------------------------------
    # AUDIT LOG
    # -----------------------------------
    AuditLog.objects.create(

        user=request.user,
        action=f"Applied for job: {job.title} (ATS: {score}%)"

    )

    # -----------------------------------
    # REDIRECT
    # -----------------------------------
    return redirect("seeker_dashboard")

# ======================================
# SEEKER DASHBOARD
# ======================================

@login_required
@role_required('seeker')
def seeker_dashboard(request):

    applications = Application.objects.filter(applicant=request.user)

    for app in applications:

        # split missing skills
        if app.missing_skills:
            app.missing_skills_list = [s.strip() for s in app.missing_skills.split(",")]
        else:
            app.missing_skills_list = []

        # calculate remaining score for chart
        app.remaining_score = 100 - app.ats_score

    return render(
        request,
        "seeker_dashboard.html",
        {
            "applications": applications
        }
    )
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg

import PyPDF2

from .models import Job, Application, AuditLog
from .decorators import role_required
from .services import (
    filter_applications_by_score,
    sort_applications_highest,
    get_average_score
)
from .utils import calculate_ats_score
from .email_utils import send_status_email


# ======================================
# SEEKER PROFILE (EDIT PROFILE)
# ======================================

@login_required
@role_required('seeker')
def seeker_profile(request):

    user = request.user

    resume_score = None
    matched_skills = []
    missing_skills = []
    rating = None

    # -----------------------------
    # CALCULATE ATS SCORE
    # -----------------------------
    if user.resume:

        try:

            resume_text = ""

            pdf = PyPDF2.PdfReader(user.resume)

            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    resume_text += text + " "

            skills_required = "python,django,sql,html,css"

            score, matched, missing = calculate_ats_score(
                resume_text,
                skills_required
            )

            resume_score = score
            matched_skills = matched
            missing_skills = missing

            # Rating system
            if score >= 80:
                rating = "strong"
            elif score >= 60:
                rating = "moderate"
            else:
                rating = "weak"

        except Exception as e:
            print("Resume parsing error:", e)

    # -----------------------------
    # UPDATE PROFILE
    # -----------------------------
    if request.method == "POST":

        new_username = request.POST.get("username")

        if new_username and new_username != user.username:

            if not request.session.get("otp_verified"):
                messages.error(request, "Please verify OTP before changing username.")
                return redirect("seeker_profile")

            # Prevent duplicate username
            if type(user).objects.filter(username=new_username).exists():
                messages.error(request, "Username already exists.")
                return redirect("seeker_profile")

            user.username = new_username
            user.save()

            request.session.pop("otp_verified", None)

            messages.success(request, "Username updated successfully.")

        # Update Resume
        if request.FILES.get("resume"):

            user.resume = request.FILES["resume"]
            user.save()

            messages.success(request, "Resume updated successfully.")

        return redirect("seeker_profile")

    return render(
        request,
        "seeker_profile.html",
        {
            "user": user,
            "resume_score": resume_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "rating": rating
        }
    )


# ======================================
# RECONSIDER APPLICATION
# ======================================

@login_required
@role_required('seeker')
def reconsider(request, app_id):

    application = get_object_or_404(
        Application,
        id=app_id,
        applicant=request.user
    )

    if application.status != "Rejected":
        messages.warning(request, "Only rejected applications can request reconsideration.")
        return redirect("seeker_dashboard")

    if application.reconsider_count >= 1:
        messages.warning(request, "You can only request reconsideration once.")
        return redirect("seeker_dashboard")

    application.reconsider_requested = True
    application.reconsider_count += 1
    application.status = "Under Review"
    application.save()

    send_status_email(
        application.job.employer.email,
        "Reconsideration Requested",
        f"{application.applicant.username} requested reconsideration for {application.job.title}"
    )

    AuditLog.objects.create(
        user=request.user,
        action=f"Requested reconsideration for {application.job.title}"
    )

    messages.success(request, "Reconsideration request submitted.")

    return redirect("seeker_dashboard")


# ======================================
# EMPLOYER DASHBOARD
# ======================================

@login_required
@role_required('employer')
def employer_dashboard(request):

    jobs = Job.objects.filter(
        employer=request.user
    ).order_by("-id")

    applications = Application.objects.filter(
        job__employer=request.user
    ).select_related("job", "applicant")

    # Score filter
    score_filter = request.GET.get("score")

    if score_filter:
        applications = filter_applications_by_score(applications, score_filter)

    # Sort by ATS
    applications = sort_applications_highest(applications)

    # Stats
    total_applications = applications.count()

    shortlisted_count = applications.filter(
        status="Shortlisted"
    ).count()

    rejected_count = applications.filter(
        status="Rejected"
    ).count()

    avg_score = get_average_score(applications)

    chart_data = {
        "shortlisted": shortlisted_count,
        "rejected": rejected_count,
        "pending": total_applications - shortlisted_count - rejected_count
    }

    return render(
        request,
        "employer_dashboard.html",
        {
            "jobs": jobs,
            "applications": applications,
            "total_applications": total_applications,
            "shortlisted_count": shortlisted_count,
            "rejected_count": rejected_count,
            "avg_score": avg_score,
            "selected_filter": score_filter,
            "chart_data": chart_data
        }
    )


# ======================================
# EMPLOYER JOB LIST
# ======================================

@login_required
@role_required('employer')
def employer_jobs(request):

    jobs = Job.objects.filter(
        employer=request.user
    ).order_by("-id")

    return render(
        request,
        "employer_jobs.html",
        {"jobs": jobs}
    )


# ======================================
# REVIEW APPLICATION
# ======================================

@login_required
@role_required('employer')
def review_application(request, app_id):

    application = get_object_or_404(
        Application,
        id=app_id,
        job__employer=request.user
    )

    matched_list = []
    missing_list = []

    if application.matched_skills:
        matched_list = [
            s.strip() for s in application.matched_skills.split(",") if s.strip()
        ]

    if application.missing_skills:
        missing_list = [
            s.strip() for s in application.missing_skills.split(",") if s.strip()
        ]

    if request.method == "POST":

        status = request.POST.get("status")
        reason = request.POST.get("reason", "").strip()
        override = request.POST.get("override")

        valid_status = ["Shortlisted", "Rejected", "Under Review"]

        if override:

            application.is_override = True
            application.status = "Shortlisted"
            application.rejection_reason = "Manually approved by employer."

        else:

            application.is_override = False

            if status not in valid_status:
                messages.error(request, "Invalid application status.")
                return redirect("employer_dashboard")

            if status == "Rejected" and not reason:
                messages.error(request, "Rejection reason is mandatory.")
                return render(
                    request,
                    "review_application.html",
                    {
                        "application": application,
                        "matched_list": matched_list,
                        "missing_list": missing_list
                    }
                )

            application.status = status
            application.rejection_reason = reason

        application.reconsider_requested = False
        application.save()

        email_message = f"""
Application Status Update

Job Title: {application.job.title}

Status: {application.status}

Reason:
{application.rejection_reason or "N/A"}
"""

        send_status_email(
            application.applicant.email,
            "Application Status Update",
            email_message
        )

        AuditLog.objects.create(
            user=request.user,
            action=f"Reviewed application of {application.applicant.username}"
        )

        messages.success(request, "Application updated successfully.")

        return redirect("employer_dashboard")

    return render(
        request,
        "review_application.html",
        {
            "application": application,
            "matched_list": matched_list,
            "missing_list": missing_list
        }
    )