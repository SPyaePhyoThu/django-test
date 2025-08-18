from django.views.generic import TemplateView

class RegisterPageView(TemplateView):
    template_name = "authentication/register.html"
