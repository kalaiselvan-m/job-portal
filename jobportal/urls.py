from django.urls import path
from . import views

urlpatterns = [

    # ====================================
    # HOME
    # ====================================
    path('', views.home, name='home'),

    # ====================================
    # AUTHENTICATION
    # ====================================
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ====================================
    # OTP EMAIL VERIFICATION
    # ====================================
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    # ====================================
    # JOB MANAGEMENT
    # ====================================
    path('post-job/', views.post_job, name='post_job'),
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),

    # ====================================
    # DASHBOARDS
    # ====================================
    path('seeker-dashboard/', views.seeker_dashboard, name='seeker_dashboard'),
    path('employer-dashboard/', views.employer_dashboard, name='employer_dashboard'),

    # ====================================
    # EMPLOYER JOB LIST (NEW)
    # ====================================
    path('employer-jobs/', views.employer_jobs, name='employer_jobs'),

    # ====================================
    # PROFILE (JOB SEEKER)
    # ====================================
    path('profile/', views.seeker_profile, name='seeker_profile'),

    # ====================================
    # APPLICATION MANAGEMENT
    # ====================================
    path('review/<int:app_id>/', views.review_application, name='review_application'),
    path('reconsider/<int:app_id>/', views.reconsider, name='reconsider'),

]