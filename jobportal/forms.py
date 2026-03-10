from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Job

from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):
    
    ROLE_CHOICES = (
        ('seeker', 'Job Seeker'),
        ('employer', 'Employer'),
    )

    role = forms.ChoiceField(choices=ROLE_CHOICES)

    # PHONE OPTIONAL
    phone = forms.CharField(
        max_length=15,
        required=False
    )

    company_name = forms.CharField(
        max_length=200,
        required=False
    )

    resume = forms.FileField(required=False)

    class Meta:
        model = User
        fields = [
            'role',
            'username',
            'email',
            'phone',
            'company_name',
            'resume',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Bootstrap styling
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })

        # Placeholders
        self.fields['username'].widget.attrs['placeholder'] = "Enter username"
        self.fields['email'].widget.attrs['placeholder'] = "Enter email"
        self.fields['phone'].widget.attrs['placeholder'] = "Enter phone number (optional)"
        self.fields['company_name'].widget.attrs['placeholder'] = "Enter company name"

        # Accept only PDF
        self.fields['resume'].widget.attrs.update({
            'accept': '.pdf'
        })

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        # Allow empty phone
        if not phone:
            return phone

        # Remove spaces
        phone = phone.strip()

        # Check digits only
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")

        # Indian phone number check
        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be 10 digits.")

        return phone

    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get("role")
        resume = cleaned_data.get("resume")
        company_name = cleaned_data.get("company_name")

        # Resume mandatory for Job Seeker
        if role == "seeker" and not resume:
            self.add_error("resume", "Resume is mandatory for Job Seekers.")

        # Company mandatory for Employer
        if role == "employer" and not company_name:
            self.add_error("company_name", "Company name is required for Employers.")

        return cleaned_data

class JobForm(forms.ModelForm):

    class Meta:
        model = Job
        fields = [
            'title',
            'description',
            'skills_required',
            'location',
            'minimum_ats_score'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })