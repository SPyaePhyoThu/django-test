from django.contrib.auth import authenticate, login
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ..serializers import LoginSerializer

class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request, 
            email=serializer.validated_data['email'], 
            password=serializer.validated_data['password']
        )

        if user is not None:
            login(request, user)
            return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        if user is None:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
