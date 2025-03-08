import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer


logger = logging.getLogger('library.books')

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username', 'unknown')
        logger.info(f"Login attempt for user: {username}")
        
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            logger.info(f"Successful login for user: {username}")
        else:
            logger.warning(f"Failed login attempt for user: {username}, status: {response.status_code}")
        
        return response



@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    if request.method == 'POST':
        username = request.data.get('username', 'unknown')
        roles = request.data.get('role', 'unknown')
        
        logger.info(f"Registration attempt for username: {username} with roles: {roles}")
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User registered successfully: {user.username} (ID: {user.id}) with role: {user.roles}")
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"Registration failed for {username} due to validation errors: {serializer.errors}")
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)