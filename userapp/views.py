from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, View, FormView, ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from .models import Review, Category, Subscription, Shop, Reservation, Favorite
from .forms import SearchForm, SignUpForm, EmailLoginForm, ReviewForm, ReservationForm, ReviewEditForm, SubscriptionForm, ProfileEditForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Avg, Q
from django.contrib import messages
from django.conf import settings
import stripe
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from .mixins import PaidMemberRequiredMixin
import json
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# Stripeの公開鍵を返すビュー
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

# 検索機能のビュー
def Search(request):
    total_hit_count = 0
    shop_info = []

    if request.method == 'GET':
        searchform = SearchForm(request.GET)
        
        print('searchform.is_valid()',searchform.is_valid())
        if searchform.is_valid():
            # 各検索パラメータを取得
            category_id = request.GET.get('selected_category', '')
            freeword = request.GET.get('freeword', '')
            region = request.GET.get('region', '')  # 地域
            price_range = request.GET.get('price_range', '')  # 価格帯
            rating = request.GET.get('rating', '')  # 評価

            query = Shop.objects.all()

            # カテゴリのフィルタリング
            if category_id:
                query = query.filter(category_id=category_id)

            # フリーワードのフィルタリング（店名で検索）
            if freeword:
                query = query.filter(name__icontains=freeword)

            # 地域のフィルタリング（住所に地域が含まれるか）
            if region:
                query = query.filter(region__icontains=region)

            # 価格帯のフィルタリング
            if price_range:
                price_range_values = price_range.split('-')
                min_price = int(price_range_values[0])
                max_price = price_range_values[1]
                if max_price:
                    max_price = int(max_price)
                    query = query.filter(price_range__gte=min_price, price_range__lte=max_price)
                else:
                    query = query.filter(price_range__gte=min_price)

            # 評価のフィルタリング（平均スコアでフィルタリング）
            if rating:
                try:
                    rating_value = int(rating)
                    query = query.annotate(avg_rating=Avg('review__score')).filter(avg_rating__gte=rating_value)
                except ValueError:
                    pass  # 無効なratingが渡された場合はフィルタを適用しない

            total_hit_count = query.count()
            shop_info = query[:10]  # 表示件数を制限

    params = {
        'total_hit_count': total_hit_count,
        'shop_info': shop_info,
        'searchform': searchform,
    }

    return render(request, 'userapp/search.html', params)

# 店舗情報の表示および操作を行うビュー
class ShopInfoView(View):
    template_name = 'userapp/shop_info.html'

    def get(self, request, shop_id):
        return self.render_shop_info(request, shop_id)

    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        if not request.user.is_authenticated:
            messages.error(request, 'この操作を行うにはログインが必要です。', extra_tags='login')
            return redirect('userapp:login')

        try:
            subscription = Subscription.objects.get(user=request.user)
            if not subscription.active:
                raise Subscription.DoesNotExist
        except Subscription.DoesNotExist:
            return redirect('userapp:subscription')

        # 各フォームの処理
        if 'review_submit' in request.POST:
            review_form = ReviewForm(data=request.POST)
            if review_form.is_valid():
                existing_review = Review.objects.filter(shop=shop, user=request.user).first()
                if existing_review:
                    messages.error(request, '既にこの店舗にレビューを投稿しています。', extra_tags='review')
                else:
                    review = Review()
                    review.shop = shop
                    review.user = request.user
                    review.score = review_form.cleaned_data['score']
                    review.comment = review_form.cleaned_data['comment']
                    review.save()
                    messages.success(request, 'レビューの投稿が完了しました。', extra_tags='review')
            else:
                messages.error(request, 'レビューの投稿にエラーがあります。', extra_tags='review')
            return redirect('userapp:shop_info', shop_id=shop_id)
        elif 'reservation_submit' in request.POST:
            reservation_form = ReservationForm(data=request.POST)
            if reservation_form.is_valid():
                reservation = reservation_form.save(commit=False)
                reservation.user = request.user
                reservation.shop = shop
                reservation.save()
                messages.success(request, '予約が完了しました。', extra_tags='reservation')
            else:
                messages.error(request, '予約の投稿にエラーがあります。', extra_tags='reservation')
            return redirect('userapp:shop_info', shop_id=shop_id)
        elif 'favorite_submit' in request.POST:
            Favorite.objects.create(shop=shop, user=request.user)
            messages.success(request, 'お気に入りに追加しました。', extra_tags='favorite')
            return redirect('userapp:shop_info', shop_id=shop_id)
        elif 'unfavorite_submit' in request.POST:
            Favorite.objects.filter(shop=shop, user=request.user).delete()
            messages.success(request, 'お気に入りから削除しました。', extra_tags='favorite')
            return redirect('userapp:shop_info', shop_id=shop_id)

        return redirect('userapp:shop_info', shop_id=shop_id)

    def render_shop_info(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        review_count = Review.objects.filter(shop=shop).count()
        score_ave = Review.objects.filter(shop=shop).aggregate(Avg('score'))
        average = score_ave['score__avg']
        average_rate = average / 5 * 100 if average else 0
        review_form = ReviewForm()
        review_list = Review.objects.filter(shop=shop)
        reservation_form = ReservationForm(initial={'shop': shop})

        is_favorite = False
        if request.user.is_authenticated:
            is_favorite = Favorite.objects.filter(shop=shop, user=request.user).exists()

        params = {
            'title': '店舗詳細',
            'review_count': review_count,
            'shop': shop,
            'review_form': review_form,
            'review_list': review_list,
            'average': average,
            'average_rate': average_rate,
            'reservation_form': reservation_form,
            'is_favorite': is_favorite
        }
        return render(request, self.template_name, params)

# ホームページの表示
class IndexView(TemplateView):
    template_name = 'userapp/index.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        searchform = SearchForm()
        pickup_list = Shop.objects.all()[:10]
        review_list = Review.objects.select_related('shop').all()[:10]
        category_list = Category.objects.all()

        context.update({
            'searchform': searchform,
            'pickup_list': pickup_list,
            'review_list': review_list,
            'category_list': category_list
        })

        return context

# 予約キャンセルのビュー
class ReservationCancelView(LoginRequiredMixin, DeleteView):
    model = Reservation
    template_name = 'userapp/reservation_confirm_cancel.html'
    success_url = reverse_lazy('userapp:subscription')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(self.request, '予約をキャンセルしました。', extra_tags='reservation')
        return redirect(success_url)

# レビュー編集のビュー
class ReviewEditView(LoginRequiredMixin, PaidMemberRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewEditForm
    template_name = 'userapp/review_form.html'

    def get_success_url(self):
        messages.success(self.request, 'レビューを更新しました。', extra_tags='review')
        return reverse('userapp:subscription')

# レビュー削除のビュー
class ReviewDeleteView(LoginRequiredMixin, PaidMemberRequiredMixin, DeleteView):
    model = Review
    template_name = 'userapp/review_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, 'レビューを削除しました。', extra_tags='review')
        return reverse('userapp:subscription')

# 新規ユーザー登録のビュー
class SignUp(CreateView):
    form_class = SignUpForm
    template_name = 'userapp/signup.html'

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        if form.is_valid():
            user = form.save()
            # Stripe Checkout Sessionを作成
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user.email,
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=request.build_absolute_uri('/success/'),
                cancel_url=request.build_absolute_uri('/cancel/'),
            )
            # 一時的にユーザー情報を保存
            Subscription.objects.create(
                user=user,
                stripe_customer_id='',
                stripe_subscription_id='',
                active=False,
            )
            return redirect(checkout_session.url)
        return render(request, 'userapp/signup.html', {'form': form})

# ログインのビュー
class Login(LoginView):
    form_class = EmailLoginForm
    template_name = 'userapp/login.html'

# サブスクリプション情報の表示ビュー
@method_decorator(login_required, name='dispatch')
class SubscriptionView(TemplateView):
    template_name = 'userapp/subscription.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            subscription = Subscription.objects.get(user=self.request.user)
            context['subscription'] = subscription
        except Subscription.DoesNotExist:
            context['subscription'] = None
            messages.error(self.request, 'この機能を使用するには有料会員登録が必要です')
        
        # 公開鍵を設定
        context["stripe_publishable_key"] = settings.STRIPE_PUBLISHABLE_KEY
        
        return context

# プロフィール編集のビュー
@method_decorator(login_required, name='dispatch')
class ProfileEditView(UpdateView):
    model = get_user_model()
    form_class = ProfileEditForm
    template_name = 'userapp/profile_edit.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, 'プロフィールを更新しました。')
        return reverse('userapp:profile')

# ログアウトのビュー
class Logout(LogoutView):
    template_name = 'userapp/logout.html'

# プロフィール表示のビュー
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'userapp/profile.html'

# マイページ表示のビュー
class MyPageView(LoginRequiredMixin, TemplateView):
    template_name = 'userapp/mypage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            subscription = Subscription.objects.get(user=self.request.user)
            context['subscription'] = subscription
        except Subscription.DoesNotExist:
            context['subscription'] = None
        return context

# お気に入り一覧のビュー
class FavoritesView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'userapp/favorites.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('shop')

# お気に入り解除のビュー
@login_required
def unfavorite_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    Favorite.objects.filter(shop=shop, user=request.user).delete()
    messages.success(request, 'お気に入りから削除しました。', extra_tags='favorite')
    return redirect('userapp:subscription')

# 予約一覧のビュー
class ReservationsView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'userapp/reservations.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

# 支払い方法のビュー
class PaymentMethodView(LoginRequiredMixin, TemplateView):
    template_name = 'userapp/payment_method.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            subscription = Subscription.objects.get(user=self.request.user)
            context['subscription'] = subscription
        except Subscription.DoesNotExist:
            context['subscription'] = None
            messages.error(self.request, 'この機能を使用するには有料会員登録が必要です')

        context["stripe_publishable_key"] = settings.STRIPE_PUBLISHABLE_KEY

        return context

# サブスクリプション支払いページのビュー
class SubscriptionPaymentView(TemplateView):
    template_name = 'userapp/subscription_payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['stripe_publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY
        return context

# 支払い成功時のビュー
def success(request):
    messages.success(request, "支払いが成功しました。")
    return render(request, 'userapp/success.html')

# 支払い失敗時のビュー
def cancel(request):
    messages.error(request, "支払いがキャンセルされました。")
    return render(request, 'userapp/cancel.html')

# サブスクリプション解除のビュー
class CancelSubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = 'userapp/cancel_subscription.html'

    def post(self, request, *args, **kwargs):
        try:
            subscription = Subscription.objects.get(user=request.user)
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            subscription.active = False
            subscription.save()
            messages.success(request, '有料会員を解約しました。', extra_tags='subscription')
        except stripe.error.InvalidRequestError as e:
            messages.error(request, f'サブスクリプションの解除に失敗しました: {str(e)}')
        except Exception as e:
            messages.error(request, f'予期しないエラーが発生しました: {str(e)}')

        return redirect('userapp:subscription')

# クレジットカード登録と支払い機能を持たせるためのビュー
@method_decorator(login_required, name='dispatch')
class SubscribeView(View):
    template_name = 'userapp/payment_method.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
        })

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            token = data.get('token')  # JavaScript側で送信されたトークンを取得
            logger.info(f"取得したtoken: {token}")

            if not token:
                return JsonResponse({'status': 'error', 'message': 'Stripe token not provided'}, status=400)

            cardholder_name = data.get('name')

            # Stripeカスタマーを作成
            customer = stripe.Customer.create(
                email=request.user.email,
                source=token,
                name=cardholder_name
            )

            # Stripeサブスクリプションを作成
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': settings.STRIPE_PRICE_ID}],
            )

            # サブスクリプションを保存
            Subscription.objects.create(
                user=request.user,
                stripe_customer_id=customer.id,
                stripe_subscription_id=subscription.id,
                active=True
            )

            messages.success(request, 'サブスクリプションの登録が完了しました。')
            return JsonResponse({'status': 'success'}, status=200)

        except stripe.error.StripeError as e:
            logger.error(e, exc_info=True)
            messages.error(request, f'エラーが発生しました: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            logger.error(e, exc_info=True)
            messages.error(request, f'予期しないエラーが発生しました: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=403)

# Checkoutセッションを作成するビュー
@csrf_exempt
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Stripe Checkoutセッションを作成
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,  # Stripeの価格ID
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=request.build_absolute_uri('/subscription/success/'),
                cancel_url=request.build_absolute_uri('/subscription/cancel/'),
            )
            return JsonResponse({
                'sessionId': checkout_session['id']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# 新規作成用
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'userapp/signup.html'

    def form_valid(self, form):
        user = form.save()
        backend = 'django.contrib.auth.backends.ModelBackend'  # ここで適切なバックエンドを指定します
        login(self.request, user, backend=backend)
        return redirect('userapp:index')

# レビュー編集のビュー
class ReviewEditView(LoginRequiredMixin, PaidMemberRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewEditForm
    template_name = 'userapp/review_form.html'

    def get_success_url(self):
        messages.success(self.request, 'レビューを更新しました。', extra_tags='review')
        return reverse('userapp:subscription')

# レビュー削除のビュー
class ReviewDeleteView(LoginRequiredMixin, PaidMemberRequiredMixin, DeleteView):
    model = Review
    template_name = 'userapp/review_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, 'レビューを削除しました。', extra_tags='review')
        return reverse('userapp:subscription')

# 新規ユーザー登録のビュー
class SignUp(CreateView):
    form_class = SignUpForm
    template_name = 'userapp/signup.html'

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        if form.is_valid():
            user = form.save()
            # Stripe Checkout Sessionを作成
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user.email,
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=request.build_absolute_uri('/success/'),
                cancel_url=request.build_absolute_uri('/cancel/'),
            )
            # 一時的にユーザー情報を保存
            Subscription.objects.create(
                user=user,
                stripe_customer_id='',
                stripe_subscription_id='',
                active=False,
            )
            return redirect(checkout_session.url)
        return render(request, 'userapp/signup.html', {'form': form})

# ログインのビュー
class Login(LoginView):
    form_class = EmailLoginForm
    template_name = 'userapp/login.html'

# サブスクリプション情報の表示ビュー
@method_decorator(login_required, name='dispatch')
class SubscriptionView(TemplateView):
    template_name = 'userapp/subscription.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            subscription = Subscription.objects.get(user=self.request.user)
            context['subscription'] = subscription
        except Subscription.DoesNotExist:
            context['subscription'] = None
            messages.error(self.request, 'この機能を使用するには有料会員登録が必要です')
        
        # 公開鍵を設定
        context["stripe_publishable_key"] = settings.STRIPE_PUBLISHABLE_KEY
        
        return context

# プロフィール編集のビュー
@method_decorator(login_required, name='dispatch')
class ProfileEditView(UpdateView):
    model = get_user_model()
    form_class = ProfileEditForm
    template_name = 'userapp/profile_edit.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, 'プロフィールを更新しました。')
        return reverse('userapp:profile')

# ログアウトのビュー
class Logout(LogoutView):
    template_name = 'userapp/logout.html'

# プロフィール表示のビュー
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'userapp/profile.html'

# マイページ表示のビュー
class MyPageView(LoginRequiredMixin, TemplateView):
    template_name = 'userapp/mypage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            subscription = Subscription.objects.get(user=self.request.user)
            context['subscription'] = subscription
        except Subscription.DoesNotExist:
            context['subscription'] = None
        return context

# お気に入り一覧のビュー
class FavoritesView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'userapp/favorites.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('shop')

# お気に入り解除のビュー
@login_required
def unfavorite_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    Favorite.objects.filter(shop=shop, user=request.user).delete()
    messages.success(request, 'お気に入りから削除しました。', extra_tags='favorite')
    return redirect('userapp:subscription')

# 予約一覧のビュー
class ReservationsView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = 'userapp/reservations.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

# 支払い方法のビュー
class PaymentMethodView(LoginRequiredMixin, TemplateView):
    template_name = 'userapp/payment_method.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            subscription = Subscription.objects.get(user=self.request.user)
            context['subscription'] = subscription
        except Subscription.DoesNotExist:
            context['subscription'] = None
            messages.error(self.request, 'この機能を使用するには有料会員登録が必要です')

        context["stripe_publishable_key"] = settings.STRIPE_PUBLISHABLE_KEY

        return context

# サブスクリプション支払いページのビュー
class SubscriptionPaymentView(TemplateView):
    template_name = 'userapp/subscription_payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY
        return context

# 支払い成功時のビュー
def success(request):
    messages.success(request, "支払いが成功しました。")
    return render(request, 'userapp/success.html')

# 支払い失敗時のビュー
def cancel(request):
    messages.error(request, "支払いがキャンセルされました。")
    return render(request, 'userapp/cancel.html')

# サブスクリプション解除のビュー
class CancelSubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = 'userapp/cancel_subscription.html'

    def post(self, request, *args, **kwargs):
        try:
            subscription = Subscription.objects.get(user=request.user)
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            subscription.active = False
            subscription.save()
            messages.success(request, '有料会員を解約しました。', extra_tags='subscription')
        except stripe.error.InvalidRequestError as e:
            messages.error(request, f'サブスクリプションの解除に失敗しました: {str(e)}')
        except Exception as e:
            messages.error(request, f'予期しないエラーが発生しました: {str(e)}')

        return redirect('userapp:subscription')

# クレジットカード登録と支払い機能を持たせるためのビュー
@method_decorator(login_required, name='dispatch')
class SubscribeView(View):
    template_name = 'userapp/payment_method.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
        })

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            token = data.get('token')  # JavaScript側で送信されたトークンを取得
            logger.info(f"取得したtoken: {token}")

            if not token:
                return JsonResponse({'status': 'error', 'message': 'Stripe token not provided'}, status=400)

            cardholder_name = data.get('name')

            # Stripeカスタマーを作成
            customer = stripe.Customer.create(
                email=request.user.email,
                source=token,
                name=cardholder_name
            )

            # Stripeサブスクリプションを作成
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': settings.STRIPE_PRICE_ID}],
            )

            # サブスクリプションを保存
            Subscription.objects.create(
                user=request.user,
                stripe_customer_id=customer.id,
                stripe_subscription_id=subscription.id,
                active=True
            )

            messages.success(request, 'サブスクリプションの登録が完了しました。')
            return JsonResponse({'status': 'success'}, status=200)

        except stripe.error.StripeError as e:
            logger.error(e, exc_info=True)
            messages.error(request, f'エラーが発生しました: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            logger.error(e, exc_info=True)
            messages.error(request, f'予期しないエラーが発生しました: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)}, status=403)

# Checkoutセッションを作成するビュー
@csrf_exempt
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Stripe Checkoutセッションを作成
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,  # Stripeの価格ID
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=request.build_absolute_uri('/subscription/success/'),
                cancel_url=request.build_absolute_uri('/subscription/cancel/'),
            )
            return JsonResponse({
                'sessionId': checkout_session['id']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# 新規作成用
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'userapp/signup.html'

    def form_valid(self, form):
        user = form.save()
        backend = 'django.contrib.auth.backends.ModelBackend'  # ここで適切なバックエンドを指定します
        login(self.request, user, backend=backend)
        return redirect('userapp:index')
