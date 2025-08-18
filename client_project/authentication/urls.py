from django.urls import path
from .views import (
    RegisterView, LoginView, RegisterPageView, LoginPageView, ComingSoonView, LogoutView,
    PasswordResetRequestView, PasswordResetConfirmView, PasswordResetRequestAPIView, PasswordResetConfirmAPIView
)

urlpatterns = [
    ##templates
    path('register/', RegisterPageView.as_view(), name='register_page'),
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('coming-soon/', ComingSoonView.as_view(), name='coming_soon'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    ## apis
    path('api/register/', RegisterView.as_view(), name='register_api'),
    path('api/login/', LoginView.as_view(), name='login_api'),
    path('api/logout/', LogoutView.as_view(), name='logout_api'),
    path('api/password-reset-request/', PasswordResetRequestAPIView.as_view(), name='password_reset_request_api'),
    path('api/password-reset-confirm/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm_api'),
]