from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'jobs'

urlpatterns = [
    # Job listings and creation.
    path('', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('companies/create/', views.company_create, name='company_create'),

    # Account access.
    path('register/', views.register, name='register'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='jobs/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Candidate and employer applications.
    path('jobs/<int:pk>/apply/', views.apply_to_job, name='apply_to_job'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path(
        'employer/applications/',
        views.employer_applications,
        name='employer_applications',
    ),
    path(
        'applications/<int:pk>/status/',
        views.application_status_update,
        name='application_status_update',
    ),
    path('applications/<int:pk>/cv/', views.application_cv, name='application_cv'),
]
