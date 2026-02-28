from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    User,
    Profile,
    Student,
    Faculty,
    Staff,
    Alumni,
    UserVerification
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'role',
        'is_approved',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'role',
        'is_approved',
        'is_staff',
        'is_active',
    )

    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'contact_number',
            )
        }),
        ('Role & Approval', {'fields': ('role', 'is_approved')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'contact_number',
                'password1',
                'password2',
                'role',
                'is_approved',
                'is_staff',
                'is_superuser',
            ),
        }),
    )
    readonly_fields = ('last_login', 'date_joined')



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'joined_date')
    search_fields = ('user__email',)



@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'verification_type',
        'is_verified',
        'submitted_at',
        'view_document',
    )

    list_filter = ('verification_type', 'is_verified')
    search_fields = ('user__email',)

    readonly_fields = (
        'user',
        'verification_type',
        'document',
        'submitted_at',
        'reviewed_at',
        'reviewed_by',
    )

    fieldsets = (
        (None, {
            'fields': ('user', 'verification_type', 'document')
        }),
        ('Review', {
            'fields': (
                'is_verified',
                'remarks',
                'reviewed_by',
                'reviewed_at',
            )
        }),
    )

    def view_document(self, obj):
        if obj.document:
            return format_html(
                '<a href="{}" target="_blank">View</a>',
                obj.document.url
            )
        return "No document"

    view_document.short_description = "Document"

# Register your models here.
# admin.site.register(User)
# admin.site.register(Profile)
# admin.site.register(UserVerification)
admin.site.register(Student)
admin.site.register(Faculty)
admin.site.register(Staff)
admin.site.register(Alumni)