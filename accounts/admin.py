# 管理画面モジュールのインポート
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm
from userapp.models import Profile

# プロフィールインラインモデル
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profiles'

# カスタムユーザ管理クラス
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'username', 'is_paid_member', 'is_staff', 'is_active']
    list_filter = ['is_paid_member', 'is_staff', 'is_active']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': (
            'is_paid_member', 
            'paid_member_since', 
            'postal_code', 
            'address', 
            'phone_number', 
            'birthday', 
            'job'
        )}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 
                'username', 
                'password1', 
                'password2', 
                'is_paid_member', 
                'paid_member_since', 
                'postal_code', 
                'address', 
                'phone_number', 
                'birthday', 
                'job',
                'is_staff', 
                'is_active'
            ),
        }),
    )

    inlines = (ProfileInline,)

# カスタムユーザモデルの登録
try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass

admin.site.register(CustomUser, CustomUserAdmin)
