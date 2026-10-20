from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    ApplicationForm,
    ApplicationStatusForm,
    CompanyForm,
    JobForm,
    RegisterForm,
)
from .models import Application, Category, Company, Job


def job_list(request):
    jobs = Job.objects.filter(is_active=True).select_related(
        'company', 'category'
    )

    category_id = request.GET.get('category', '').strip()
    city = request.GET.get('city', '').strip()
    min_salary = request.GET.get('min_salary', '').strip()

    if category_id.isdecimal():
        jobs = jobs.filter(category_id=int(category_id))

    if city:
        jobs = jobs.filter(city__icontains=city)

    error = ''
    if min_salary:
        try:
            salary = Decimal(min_salary)

            if not salary.is_finite() or salary < 0:
                raise ValueError

            jobs = jobs.filter(salary__gte=salary)
        except (InvalidOperation, ValueError):
            error = 'Minimum maaş üçün sıfır və ya müsbət rəqəm daxil et.'

    return render(request, 'jobs/job_list.html', {
        'jobs': jobs,
        'categories': Category.objects.all().order_by('name'),
        'selected_category': category_id,
        'city': city,
        'min_salary': min_salary,
        'error': error,
    })


def job_detail(request, pk):
    job = get_object_or_404(
        Job.objects.select_related('company', 'category'),
        pk=pk,
        is_active=True,
    )

    return render(request, 'jobs/job_detail.html', {
        'job': job,
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('jobs:job_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('jobs:job_list')
    else:
        form = RegisterForm()

    return render(request, 'jobs/register.html', {
        'form': form,
    })


@login_required
def apply_to_job(request, pk):
    job = get_object_or_404(
        Job.objects.select_related('company'),
        pk=pk,
        is_active=True,
    )

    if job.company.owner_id == request.user.id:
        messages.error(
            request,
            'Öz şirkətinin elanına müraciət edə bilməzsən.',
        )
        return redirect('jobs:job_detail', pk=job.pk)

    if Application.objects.filter(
        job=job,
        candidate=request.user,
    ).exists():
        messages.info(
            request,
            'Bu elana artıq müraciət etmisən.',
        )
        return redirect('jobs:my_applications')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user

            try:
                with transaction.atomic():
                    application.save()
            except IntegrityError:
                # Paralel göndərilən müraciətdə təkrarı yoxla.
                if application.cv._committed:
                    application.cv.delete(save=False)

                if not Application.objects.filter(
                    job=job,
                    candidate=request.user,
                ).exists():
                    raise

                messages.info(
                    request,
                    'Bu elana artıq müraciət etmisən.',
                )
            else:
                messages.success(
                    request,
                    'Müraciətin uğurla göndərildi.',
                )

            return redirect('jobs:my_applications')
    else:
        form = ApplicationForm()

    return render(request, 'jobs/apply.html', {
        'job': job,
        'form': form,
    })


@login_required
def my_applications(request):
    applications = Application.objects.filter(
        candidate=request.user,
    ).select_related('job', 'job__company')

    return render(request, 'jobs/my_applications.html', {
        'applications': applications,
    })


@login_required
def company_create(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)

        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()

            messages.success(request, 'Şirkət yaradıldı.')
            return redirect('jobs:job_create')
    else:
        form = CompanyForm()

    return render(request, 'jobs/company_form.html', {
        'form': form,
    })


@login_required
def job_create(request):
    if not Company.objects.filter(owner=request.user).exists():
        messages.info(
            request,
            'Elan yerləşdirmək üçün əvvəlcə şirkət yarat.',
        )
        return redirect('jobs:company_create')

    if request.method == 'POST':
        form = JobForm(request.POST, user=request.user)

        if form.is_valid():
            job = form.save()

            messages.success(request, 'İş elanı yaradıldı.')
            return redirect('jobs:job_detail', pk=job.pk)
    else:
        form = JobForm(user=request.user)

    return render(request, 'jobs/job_form.html', {
        'form': form,
    })


@login_required
def employer_applications(request):
    applications = Application.objects.filter(
        job__company__owner=request.user,
    ).select_related(
        'candidate',
        'job',
        'job__company',
    )

    return render(request, 'jobs/employer_applications.html', {
        'applications': applications,
        'status_choices': Application.Status.choices,
    })


@login_required
@require_POST
def application_status_update(request, pk):
    application = get_object_or_404(
        Application,
        pk=pk,
        job__company__owner=request.user,
    )

    form = ApplicationStatusForm(
        request.POST,
        instance=application,
    )

    if form.is_valid():
        form.save()
        messages.success(request, 'Status yeniləndi.')
    else:
        messages.error(request, 'Düzgün status seç.')

    return redirect('jobs:employer_applications')


@login_required
def application_cv(request, pk):
    application = get_object_or_404(
        Application.objects.select_related('job__company'),
        pk=pk,
    )

    is_candidate = application.candidate_id == request.user.id
    is_owner = application.job.company.owner_id == request.user.id

    if not (is_candidate or is_owner):
        raise Http404

    if not application.cv:
        raise Http404('CV tapılmadı.')

    try:
        cv_file = application.cv.open('rb')
    except FileNotFoundError:
        raise Http404('CV faylı tapılmadı.')

    return FileResponse(
        cv_file,
        as_attachment=True,
        filename=f'cv-{application.pk}.pdf',
        content_type='application/pdf',
    )
