from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.models import TokenProxy

from .models import Game


class GameModelAdmin(admin.ModelAdmin):
    readonly_fields = ['status']
    list_filter = ()
    list_display = ('uri', 'owner', 'lang', 'status')
    ordering = ('id',)
    filter_horizontal = ()
    change_form_template = 'change_form.html'

    def has_add_permission(self, request, obj=None):
        return False


class UserModelAdmin(UserAdmin):
    fieldsets = (
        ('', {'fields': ('username', 'email', 'password', 'is_staff')}),
    )
    list_filter = ()
    list_display = ('username', 'email', 'is_staff')
    ordering = ('username',)
    filter_horizontal = ()
    search_fields = ()
    change_form_template = "change_form.html"

    def has_add_permission(self, request, obj=None):
        return False


admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.unregister(TokenProxy)
admin.site.register(User, UserModelAdmin)
admin.site.register(Game, GameModelAdmin)
