from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
# Get the current custom user model
User = get_user_model()


class UserAdmin(BaseUserAdmin):
    """
    Custom ModelAdmin class to show our Custom User Model in Admin Panel.
    Without this the fields in User Model are shown randomly in the Admin Page. 
    This also allows us to define sections that we wish to show.
    The ModelAdmin and Model are linked to each other in the 'admin.site.register' call.
    """
    
    fieldsets = (
        (None, {'fields': ('email', 'password', 'name', 'last_login')}),
        ('Organization', {'fields':('org',)}),
        ('Permissions', {'fields': (
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2')
            }
        ),
    )

    list_display = ('email', 'name', 'is_staff', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(User, UserAdmin)
