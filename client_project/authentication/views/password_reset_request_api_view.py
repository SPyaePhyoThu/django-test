from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..serializers import PasswordResetRequestSerializer

class PasswordResetRequestAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'If an account with that email exists, a password reset link has been sent.'}, status=status.HTTP_200_OK)
