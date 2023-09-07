from django.urls import path

from .views import index_view, invoice_view

urlpatterns = [
    path("", index_view),
    # path("invoice/", invoice_view)
]
