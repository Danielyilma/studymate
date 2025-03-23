from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from UserAccountManager.models import User

class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ['email', 'is_staff', 'is_superuser', 'is_active']
    list_filter = ['is_staff']

    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Personal info", {"fields": ['first_name', 'last_name', 'is_staff', 'is_superuser']}),
        ('Groups', {'fields': ('groups',)}),
        ("Permissions", {"fields": ["user_permissions", 'is_active']}),
    ]

    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "password1", "password2"],
            },
        ),
    ]

    search_fields = ["email"]
    ordering = ["email"]
    filter_horizontal = []

admin.site.register(User, UserAdmin)
