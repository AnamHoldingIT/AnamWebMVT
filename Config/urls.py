"""
URL configuration for Config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from errors import views as errors_view
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404
from .sitemaps import StaticViewSitemap
from django.contrib.sitemaps.views import sitemap

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls', namespace='home')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('admin_panal/', include('admin_panel.urls', namespace='admin_panel')),
    path('zlinks/', include('zlink.urls', namespace='zlink')),
    path('core/', include('errors.urls', namespace='core')),
    path('portfolio/', include('portfolio.urls', namespace='portfolio')),
    path('users_panel/', include('worklog.urls', namespace='worklog')),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django_sitemap"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = errors_view.PageNotFound.as_view()

urlpatterns += [
    path("robots.txt", TemplateView.as_view(
        template_name="robots.txt",
        content_type="text/plain"
    )),
]
