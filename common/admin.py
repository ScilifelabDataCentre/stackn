from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User

from .models import EmailVerificationTable, MaintenanceMode, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class EmailVerificationTableInline(admin.StackedInline):
    model = EmailVerificationTable
    can_delete = True
    verbose_name_plural = "EmailVerificationTable"
    fk_name = "user"


class UserAdmin(DefaultUserAdmin):
    inlines = (UserProfileInline, EmailVerificationTableInline)
    list_display = ("email", "first_name", "last_name", "is_active", "is_staff", "get_affiliation", "date_joined")
    list_select_related = ("userprofile",)

    def get_affiliation(self, instance):
        return instance.userprofile.affiliation

    get_affiliation.short_description = "Affiliation"  # type: ignore


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(MaintenanceMode)

# Register your models here.
