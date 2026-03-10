from django.db.models import Avg


# ======================================
# FILTER APPLICATIONS BY SCORE
# ======================================

def filter_applications_by_score(applications, score_filter=None):

    if not score_filter or score_filter == "all":
        return applications

    if score_filter == "80":
        return applications.filter(ats_score__gte=80)

    if score_filter == "60":
        return applications.filter(
            ats_score__gte=60,
            ats_score__lt=80
        )

    if score_filter == "low":
        return applications.filter(ats_score__lt=60)

    return applications


# ======================================
# SORT APPLICATIONS BY HIGHEST SCORE
# ======================================

def sort_applications_highest(applications):
    return applications.order_by('-ats_score')


# ======================================
# PASS / FAIL COUNT
# ======================================

def get_pass_fail_counts(applications):

    passed = applications.filter(
        status__in=['Under Review', 'Shortlisted']
    ).count()

    failed = applications.filter(
        status='Rejected'
    ).count()

    return passed, failed


# ======================================
# GET AVERAGE ATS SCORE
# ======================================

def get_average_score(applications):

    average = applications.aggregate(
        avg_score=Avg('ats_score')
    )['avg_score']

    if average is None:
        return 0

    return round(average, 2)