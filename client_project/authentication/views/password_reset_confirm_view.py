from django.views.generic import TemplateView

class PasswordResetConfirmView(TemplateView):
    template_name = "authentication/password_reset_confirm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['uidb64'] = self.kwargs['uidb64']
        context['token'] = self.kwargs['token']
        return context
