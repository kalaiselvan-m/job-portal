from django.contrib import admin
from .models import User, Job, Application, AuditLog


# =========================
# USER ADMIN
# =========================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        'username',
        'email',
        'role',
        'company_name',
        'is_verified',
        'is_active'
    )

    list_filter = (
        'role',
        'is_verified',
        'is_active'
    )

    search_fields = (
        'username',
        'email',
        'company_name'
    )

    ordering = ('username',)


# =========================
# JOB ADMIN
# =========================

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'employer',
        'location',
        'minimum_ats_score',
        'created_at',
        'is_active'
    )

    list_filter = (
        'location',
        'is_active'
    )

    search_fields = (
        'title',
        'location',
        'employer__username',
        'employer__company_name'
    )

    ordering = ('-created_at',)


# =========================
# APPLICATION ADMIN
# =========================

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):

    list_display = (
        'applicant',
        'job',
        'ats_score',
        'status',
        'is_override',
        'reconsider_requested',
        'applied_at'
    )

    list_filter = (
        'status',
        'is_override',
        'reconsider_requested'
    )

    search_fields = (
        'applicant__username',
        'job__title'
    )

    ordering = ('-applied_at',)

    readonly_fields = (
        'ats_score',
        'matched_skills',
        'missing_skills',
        'applied_at'
    )


# =========================
# AUDIT LOG ADMIN
# =========================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'action',
        'timestamp'
    )

    search_fields = (
        'user__username',
        'action'
    )

    ordering = ('-timestamp',)