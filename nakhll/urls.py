import email
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from nakhll import settings
from . import setup as nakhll_setup
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# from reports.admin import reports_admin_site
nakhll_setup.seutp()
schema_view = get_schema_view(
    openapi.Info(
        title="Nakhll API",
        default_version='v1',
        description="This is the API for Nakhll, an online marketplace.",
        terms_of_service="https://www.google.com/policies/terms/",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,), # TODO: change to IsAuthenticated
)

view_urls = [
    path('logintowebsite/', admin.site.urls),
    # path('reportspanel/', reports_admin_site.urls),
    # path('accounting/', include('accounting.urls', namespace='accounting')),
    path('torob/', include('torob_api.urls', namespace='torob')),
    path('goto/', include('url_redirector.urls', namespace='url_redirector')),
    path('sms/', include('sms.urls')),
    path('payoff/', include('payoff.urls', namespace='payoff')),
    path('', include('nakhll_market.view_urls', namespace='nakhll_market')),
    path('', include('django_prometheus.urls')),
]

api_urls = [
    path('auth/', include('nakhll_auth.auth_urls')),
    path('profile/', include('nakhll_auth.profile_urls')),
    path('lists/', include('custom_list.urls')),
    path('shop/', include('shop.urls')),
    path('invoices/', include('invoice.urls')),
    path('cart/', include('cart.urls')),
    path('logistic/', include('logistic.urls')),
    path('', include('restapi.urls', namespace='restapi')),
    path('', include('nakhll_market.api_urls', namespace='nakhll_market_api')),
]

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', include(view_urls)),
    path('api/v1/', include(api_urls)),
]

if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
