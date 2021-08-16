from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import InvoiceViewSet

invoice_router = DefaultRouter()
invoice_router.register('invoice', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('api/', include(invoice_router)),
]
