from django.shortcuts import render
from django.core.handlers.wsgi import WSGIRequest

from .models import Member


def index_view(request: WSGIRequest):
    member = Member.objects.filter(user_id=request.user.pk).first()
    return render(request, "sapp_library/index.html", {"member": member})

def invoice_view(request: WSGIRequest):
    return render(request, "sapp_library/invoice.html")
