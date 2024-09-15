# mixins.py
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from .models import Subscription  # 追加: Subscriptionモデルのインポート

class PaidMemberRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is a paid member."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        try:
            subscription = request.user.subscription
            if not subscription.active:
                messages.error(request, 'この機能は有料会員のみ利用可能です。')
                return redirect(reverse('userapp:subscription'))
        except Subscription.DoesNotExist:
            messages.error(request, 'この機能は有料会員のみ利用可能です。')
            return redirect(reverse('userapp:subscription'))
        return super().dispatch(request, *args, **kwargs)
