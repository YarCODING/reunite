from django.contrib import admin
from .models import Profile
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied

admin.site.register(Profile)

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        return qs.filter(is_staff=False, is_superuser=False) | qs.filter(id=request.user.id)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        
        if not request.user.is_superuser:
            critical_fields = ['is_staff', 'is_superuser', 'groups', 'user_permissions']
            return list(readonly_fields) + critical_fields
            
        return readonly_fields

    def has_delete_permission(self, request, obj=None):
        if obj and (obj.is_staff or obj.is_superuser):
            if not request.user.is_superuser:
                return False
                
        return super().has_delete_permission(request, obj)
    
    def delete_model(self, request, obj):
        if obj.is_staff or obj.is_superuser:
            raise PermissionDenied("Deleting staff and superuser accounts is prohibited.")
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        protected_queryset = queryset.filter(is_superuser=True) | queryset.filter(is_staff=True)
        protected_count = protected_queryset.count()
        
        if protected_count > 0:
            queryset = queryset.exclude(id__in=protected_queryset.values_list('id', flat=True))
            
            self.message_user(
                request, 
                f"Warning: {protected_count} users (staff or superusers) were skipped. "
                f"Only regular users were removed.", 
                messages.WARNING
            )

        super().delete_queryset(request, queryset)