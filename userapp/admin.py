# Djangoの管理画面の登録に必要なモジュールをインポート
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
# 管理画面に登録するモデルをインポート
from .models import Category, Review, Shop, Subscription, Profile

# カテゴリモデルの管理画面設定
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # 一覧表示の際に表示するフィールド
    list_display = ('category_l', 'name')
    # 詳細編集画面へのリンクを設定するフィールド
    list_display_links = ('category_l',)
    # 一覧画面で編集可能にするフィールド
    list_editable = ('name',)

# レビューモデルの管理画面設定
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # 一覧表示の際に表示するフィールド
    list_display = ('shop', 'user', 'score')
    # 詳細編集画面へのリンクを設定するフィールド
    list_display_links = ('shop',)
    # 一覧画面で編集可能にするフィールド
    list_editable = ('score',)

# 店舗モデルの管理画面設定
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    # 一覧表示の際に表示するフィールド
    list_display = ('name', 'category', 'address', 'price_range')
    # 検索可能なフィールド
    search_fields = ('name', 'address', 'price_range', 'category__name')
    # フィルター可能なフィールド
    list_filter = ('category',)

# サブスクリプションモデルの管理画面設定
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    # 一覧表示の際に表示するフィールド
    list_display = ('user', 'stripe_customer_id', 'stripe_subscription_id', 'active')
    # 詳細編集画面へのリンクを設定するフィールド
    list_display_links = ('user',)
    # 一覧画面で編集可能にするフィールド
    list_editable = ('active',)

# プロフィールモデルの管理画面設定
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # 一覧表示の際に表示するフィールド
    list_display = ('user', 'user_type', 'username_kana', 'post_code', 'address', 'tel', 'birth_date', 'business')
    # 検索可能なフィールド
    search_fields = ('user__username', 'user__email', 'username_kana', 'post_code', 'address', 'tel', 'business')
    # フィルター可能なフィールド
    list_filter = ('user_type',)

# カスタムユーザーモデルの管理画面設定
User = get_user_model()

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profiles'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# カスタムユーザーモデルの登録（すでに登録されている場合は再登録しない）
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.register(User, UserAdmin)
except admin.sites.AlreadyRegistered:
    pass
