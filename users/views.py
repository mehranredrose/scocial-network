from friend.models import FriendList, FriendRequest
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, UserEnterVerifyCodeForm, UserLoginForm,UserResetPasswordForm
from .models import Profile, User
from django.contrib.auth import views as auth_views
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.dispatch import receiver 
from django.contrib.auth.signals import user_logged_in, user_logged_out
from notification.models import Notification
import requests
from django.urls import reverse_lazy
from django.conf import settings
from friend.utils import get_friend_request_or_false
from friend.friend_request_status import FriendRequestStatus
from extensions.mixins import NotLoginMixin
from django.views import View
from django.db import IntegrityError
from .services import register_user, send_otp
from .selectors import *

@receiver(user_logged_in)
def got_online(sender, user, request, **kwargs):    
    user.profile.is_online = True
    user.profile.save()

@receiver(user_logged_out)
def got_offline(sender, user, request, **kwargs):   
    user.profile.is_online = False
    user.profile.save()



""" Following and Unfollowing users """
@login_required
def follow_unfollow_profile(request):
    if request.method == 'POST':
        my_profile = Profile.objects.get(user = request.user)
        pk = request.POST.get('profile_pk')
        obj = Profile.objects.get(pk=pk)

        if obj.user in my_profile.following.all():
            my_profile.following.remove(obj.user)
            notify = Notification.objects.filter(sender=request.user, notification_type=2)
            notify.delete()
        else:
            my_profile.following.add(obj.user)
            notify = Notification(sender=request.user, user=obj.user, notification_type=2)
            notify.save()
        return redirect(request.META.get('HTTP_REFERER'))
    return redirect('profile-list-view')


""" User account creation """
class UserRegisterView(NotLoginMixin, View):
    form_class = UserRegisterForm
    template_name = 'users/register.html'

    def get(self, request):
        form = self.form_class
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            request.session['user_registration_info'] = {
                'phone_number': form.cleaned_data['phone_number'],
                'email': form.cleaned_data['email'],
                'username': form.cleaned_data['username'],
                'password': form.cleaned_data['password'],
            }
            send_otp(phone_number=form.cleaned_data['phone_number'])
            messages.success(request, 'we sent you a code', 'success')
            return redirect('verify_code')
        return render(request, self.template_name, {'form': form})


class UserVerifyCodeView(NotLoginMixin, View):
    form_class = UserEnterVerifyCodeForm
    template_name = 'users/verify.html'

    def get(self, request):
        form = self.form_class
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        user_session = request.session.get('user_registration_info')
        code_instance = get_otp_code(phone_number=user_session.get('phone_number'))

        if code_instance is None:
            messages.error(request, 'this code is wrong', 'danger')
            return redirect('user_register')

        if form.is_valid():
            clean_data = form.cleaned_data
            if int(clean_data['code']) == code_instance.code:
                try:
                    register_user(email=user_session['email'], phone_number=user_session['phone_number'],
                                  username=user_session['username'], password=user_session['password'],
                                  bio=user_session.get('bio') if user_session.get('bio') else '', )
                    code_instance.delete()
                    messages.success(request, 'registration successfully', 'success')
                    return redirect('user_login')
                except IntegrityError:
                    messages.error(request, 'Internal server error ', 'danger')
                    return redirect('user_register')
            messages.error(request, 'this code is wrong', 'danger')
            return redirect('verify_code')

        return redirect('user_register')


class UserLoginView(NotLoginMixin, View):
    form_class = UserLoginForm
    template_name = 'users/login.html'

    def get(self, request):
        form = self.form_class
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            clean_data = form.cleaned_data
            user = authenticate(request, email=clean_data['email'], password=clean_data['password'])
            if user is not None:
                login(request, user)
                messages.success(request, 'you logged in successfully', 'info')
                return redirect('blog-home')
            messages.error(request, 'phone or password is wrong', 'danger')
            return render(request, self.template_name, {'form': form})
        return redirect('user_login')


class UserLogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.success(request, 'you logged out successfully', 'success')
        return redirect('user_login')

""" User profile """
@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f"Your account has been updated!")
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'u_form':u_form,
        'p_form':p_form
    }

    return render(request, 'users/profile.html', context)


""" Creating a public profile view """
def public_profile(request, username):
    user = User.objects.get(username=username)
    return render(request, 'users/public_profile.html', {"cuser":user})


""" All user profiles """
class ProfileListView(LoginRequiredMixin,ListView):
    model = Profile
    template_name = "users/all_profiles.html"
    context_object_name = "profiles"

    def get_queryset(self):
        return Profile.objects.all().exclude(user=self.request.user)

""" User profile details view """
class ProfileDetailView(LoginRequiredMixin,DetailView):
    model = Profile
    template_name = "users/user_profile_details.html"
    context_object_name = "profiles"

    def get_queryset(self):
        return Profile.objects.all().exclude(user=self.request.user)

    def get_object(self,**kwargs):
        pk = self.kwargs.get("pk")
        view_profile = Profile.objects.get(pk=pk)
        return view_profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        view_profile = self.get_object()
        my_profile = Profile.objects.get(user=self.request.user)
        if view_profile.user in my_profile.following.all():
            follow = True
        else:
            follow = False
        context["follow"] = follow

        # FRIENDS START

        account = view_profile.user
        try:
            friend_list = FriendList.objects.get(user=account)
        except FriendList.DoesNotExist:
            friend_list = FriendList(user=account)
            friend_list.save()
        friends = friend_list.friends.all()
        context['friends']=friends

        is_self = True
        is_friend = False
        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
        friend_requests = None
        user=self.request.user
        if user.is_authenticated and user!=account:
            is_self = False
            if friends.filter(pk=user.id):
                is_friend = True
            else:
                is_friend = False
                # CASE 1: request from them to you
                if get_friend_request_or_false(sender=account, receiver=user) != False:
                    request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                    context['pending_friend_request_id'] = get_friend_request_or_false(sender=account, receiver=user).pk
                # CASE 2: request you sent to them
                elif get_friend_request_or_false(sender=user, receiver=account) != False:
                    request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
                # CASE 3: no request has been sent
                else:
                    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value

        elif not user.is_authenticated:
            is_self = False
        else:
            try:
                friend_requests = FriendRequest.objects.filter(receiver=user, is_active=True)
            except:
                pass
        context['request_sent'] = request_sent
        context['is_friend'] = is_friend
        context['is_self'] = is_self
        context['friend_requests'] = friend_requests
        # FRIENDS END
        
        return context

# ForgotPassword
class UserPasswordResetView(NotLoginMixin, auth_views.PasswordResetView):
    template_name = 'users/password_reset.html'
    success_url = reverse_lazy('users/password_reset_done')
    email_template_name = 'users/password_reset_email.html'


class UserPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'


class UserPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users/password_reset_complete')
    #ToDO check these reverse lazy they are like redirect

class UserPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'


class UserResetPassword(LoginRequiredMixin, View):
    form_class = UserResetPasswordForm
    template_name = 'users/password_reset_form.html'

    def get(self, request):
        form = self.form_class(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(data=request.POST)
        if form.is_valid():
            user = get_user(email=request.user.email)
            user.set_password(form.cleaned_data.get('new_password'))
            user.save()
            messages.success(request, 'update information successfully', 'success')
            return redirect('user_setting')
        messages.error(request, form.errors, 'danger')
        return redirect('reset_password')
