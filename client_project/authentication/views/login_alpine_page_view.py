from django.views.generic import TemplateView

class LoginAlpinePageView(TemplateView):
    template_name = "authentication/login_alpine.html"
