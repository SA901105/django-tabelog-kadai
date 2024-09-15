from django.db import models
from django.contrib.auth.models import AbstractUser


# カスタムユーザー　有料会員定義
class CustomUser(AbstractUser):
    is_paid_member = models.BooleanField(default=False)
    paid_member_since = models.DateTimeField(null=True, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    birthday = models.DateField(null=True, blank=True)
    job = models.CharField(max_length=50, blank=True)


