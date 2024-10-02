from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views  # パスワードリセット用のビューをインポート

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('userapp.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # 既存の認証関連URL
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),  # パスワードリセットのリクエスト
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),  # リセットメール送信後の確認ページ
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # リセット用のリンクをクリックした後のページ
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),  # パスワード変更後の確認ページ
]
