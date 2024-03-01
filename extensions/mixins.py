from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.views import View


class NotLoginMixin(AccessMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_admin:
            return redirect('home:home')
        return super().dispatch(request, *args, **kwargs)
