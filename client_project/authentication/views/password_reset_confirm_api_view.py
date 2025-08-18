from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..serializers import PasswordResetConfirmSerializer

class PasswordResetConfirmAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
