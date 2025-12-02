from rest_framework.views import APIView
from .serializers import UserRegisterSerializer, ChangePasswordSerializer, CustomTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
import logging

logger = logging.getLogger(__name__)

class UserRegisterView(APIView):
    serializer_class = UserRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def get(self, request, *args, **kwargs):
        return Response()

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except Exception as e:
            logger.exception('Error during token creation')
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if response.status_code != status.HTTP_200_OK:
            return response
        
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')
        
        if not access_token and refresh_token:
            return Response({"error": "Tokens not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=3600,
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=3600*24*7,
            )
            del response.data['access']
            del response.data['refresh']
        except Exception:
            logger.exception('Error setting auth cookies')
            return Response({"error": "Failed to set authentication cookies"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
        response.data['message'] = "Login successful"
        return response
        
class CustomTokenRefreshView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                raise AuthenticationFailed("No refresh token found in cookies")

            serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)

            access_token = serializer.validated_data['access']
            response = Response({"message": "Token refreshed successfully"}, status=status.HTTP_200_OK)
            
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=False,
                samesite="Lax", 
                max_age=3600,
            )
            return response
        
        except Exception as e:
            logger.exception("Unexpected error during token refresh")
            raise AuthenticationFailed("No refresh token found in cookies")
        

class ChangePasswordView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            logger.exception('Error while blacklisting refresh token')
            return Response('Error while blacklisting refresh token')

        try:
            user.set_password(serializer.validated_data['new_password'])
            user.save()
        except Exception:
            logger.exception('Failed to update password')
            return Response({"error": "Failed to change password"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        refresh_token = RefreshToken.for_user(user)
        access_token = str(refresh_token.access_token)

        response = Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
    
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600,
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600*24*7,
        )

        return response

class LogOutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({"error": "No refresh token found"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            logger.exception("Token blacklist failed")
        
        response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response