from django.contrib.auth import logout
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
