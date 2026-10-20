from pathlib import Path

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Application, Company, Job


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cv', 'cover_letter']
        labels = {
            'cv': 'CV (PDF, maksimum 5 MB)',
            'cover_letter': 'Müraciət məktubu',
        }
        widgets = {
            'cv': forms.ClearableFileInput(
                attrs={'accept': '.pdf'}
            ),
            'cover_letter': forms.Textarea(
                attrs={'rows': 5}
            ),
        }

    def clean_cv(self):
        cv = self.cleaned_data['cv']

        if Path(cv.name).suffix.lower() != '.pdf':
            raise forms.ValidationError(
                'CV-ni PDF formatında yüklə.'
            )

        if cv.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                'CV faylı maksimum 5 MB ola bilər.'
            )

        signature = cv.read(5)
        cv.seek(0)

        if signature != b'%PDF-':
            raise forms.ValidationError(
                'Yüklənən fayl PDF formatına uyğun deyil.'
            )

        return cv


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'city', 'website']
        labels = {
            'name': 'Şirkətin adı',
            'description': 'Şirkət haqqında',
            'city': 'Şəhər',
            'website': 'Veb-sayt',
        }


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'company',
            'category',
            'title',
            'description',
            'city',
            'salary',
        ]
        labels = {
            'company': 'Şirkət',
            'category': 'Sahə',
            'title': 'Vəzifə',
            'description': 'İş haqqında',
            'city': 'Şəhər',
            'salary': 'Aylıq maaş (AZN)',
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['company'].queryset = Company.objects.filter(
            owner=user,
        )


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status']
        labels = {
            'status': 'Müraciət statusu',
        }
