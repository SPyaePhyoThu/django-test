from django.views.generic import TemplateView

class PasswordResetRequestView(TemplateView):
    template_name = "authentication/password_reset_request.html"
