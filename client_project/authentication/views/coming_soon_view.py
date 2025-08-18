from django.views.generic import TemplateView

class ComingSoonView(TemplateView):
    template_name = "main/coming_soon.html"
