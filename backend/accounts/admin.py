from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import AdminUserChangeForm, AdminUserCreationForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm
    ordering = ('email',)
    list_display = (
        'email', 'first_name', 'last_name', 'kind', 'status',
        'is_active', 'is_staff', 'is_superuser',
    )
    list_filter = ('kind', 'status', 'is_active', 'is_demo', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('is_staff', 'last_login', 'created_at', 'updated_at')
    filter_horizontal = ('groups', 'user_permissions')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal information', {'fields': ('first_name', 'last_name')}),
        ('Access', {
            'fields': (
                'kind', 'status', 'is_active', 'is_demo', 'is_staff',
                'is_superuser', 'groups', 'user_permissions',
            ),
        }),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'kind', 'status',
                'is_active', 'is_demo', 'is_superuser', 'groups',
                'user_permissions', 'password1', 'password2',
            ),
        }),
    )
