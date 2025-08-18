from rest_framework import serializers
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from ..models import User

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            request = self.context.get('request')
            reset_link = request.build_absolute_uri(f'/auth/password-reset-confirm/{uid}/{token}/')
            print(f'Password reset link: {reset_link}')

            send_mail(
                subject='Password Reset Request',
                message=f'Click the link to reset your password:\n{reset_link}',
                from_email='noreply@yourapp.com',
                recipient_list=[email],
                fail_silently=False,
            )
