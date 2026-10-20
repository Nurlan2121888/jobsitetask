from django.contrib import admin

from .models import Application, Category, Company, Job


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'city')
    search_fields = ('name', 'city', 'owner__username')
    list_filter = ('city',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company',
        'category',
        'city',
        'salary',
        'is_active',
        'created_at',
    )
    list_filter = ('category', 'city', 'is_active')
    search_fields = ('title', 'company__name', 'description')
    list_editable = ('is_active',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('candidate__username', 'job__title')
    list_editable = ('status',)
    readonly_fields = ('created_at',)