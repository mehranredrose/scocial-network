from django.urls import path
from . import views

urlpatterns = [
    
    # Authentication - Authorization
    path('register/', views.UserRegisterView.as_view(), name='user_register'),
    path('verify/', views.UserVerifyCodeView.as_view(), name='verify_code'),
    path('profile/', views.profile, name='profile'),
    path('login/', views.UserLoginView.as_view(), name='user_login'),
    path('logout/', views.UserLogoutView.as_view(), name='user_logout'),
    # forgot password :
    path('password-reset/', views.UserPasswordResetView.as_view(template_name='users/password_reset.html'), name='reset_password'),
    path('password-reset/done/', views.UserPasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.UserPasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', views.UserPasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
    
    path('all/', views.ProfileListView.as_view(), name='profile-list-view'),
    path('follow/', views.follow_unfollow_profile, name='follow-unfollow-view'),
    path('<int:pk>/', views.ProfileDetailView.as_view(), name='profile-detail-view'),
    path('public-profile/<str:username>/', views.public_profile, name='public-profile'),
    
]