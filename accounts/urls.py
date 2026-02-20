from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/toggle_privacy/', views.toggle_privacy, name='toggle_privacy'),
    path('profile/send-otp/', views.send_otp_email, name='send_otp_email'),
    path('profile/verify-otp/', views.verify_otp, name='verify_otp'),
    path('profile/set-password/', views.set_new_password, name='set_new_password'),
    path('profile/email/send-current/', views.send_current_email_otp, name='send_current_email_otp'),
    path('profile/email/verify-current/', views.verify_current_email_otp, name='verify_current_email_otp'),
    path('profile/email/send-new/', views.send_new_email_otp, name='send_new_email_otp'),
    path('profile/email/save-new/', views.verify_and_save_new_email, name='verify_and_save_new_email'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('forgot_password/', views.forgot_password_page, name='forgot_password'),
    path('forgot_password/send-otp/', views.send_reset_otp, name='send_reset_otp'),
    path('forgot_password/verify-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('forgot_password/save-password/', views.save_new_password, name='save_new_password'),
]
