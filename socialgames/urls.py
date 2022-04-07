from django.contrib import admin
from django.urls import include, path

admin.site.index_template = 'index.html'
admin.site.site_header = "SocialGames administration"
admin.site.site_title = "SocialGames administration"
admin.site.index_title = "Admin panel"
admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('api/', include('game.urls')),
]
