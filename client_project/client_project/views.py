from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse

def root_redirect_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('/auth/coming-soon/')
    else:
        return redirect('/auth/login/')
