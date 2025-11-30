from django.urls import path
from . import views
from rest_framework_simplejwt import views as tokenviews

app_name = 'account'

urlpatterns = [
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.UserRegisterView.as_view(), name='user_register'),
    path('logout/', views.LogOutView.as_view(), name='user_logout'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
]