from django import forms
from .models import Category, Review, Reservation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

SCORE_CHOICES = [
    ('1', '★'),
    ('2', '★★'),
    ('3', '★★★'),
    ('4', '★★★★'),
    ('5', '★★★★★'),
]

PRICE_CHOICES = [
    ('0-999', '0円〜999円'),
    ('1000-2999', '1000円〜2999円'),
    ('3000-4999', '3000円〜4999円'),
    ('5000-9999', '5000円〜9999円'),
]

REGION_CHOICES = [
    ('北区', '北区'),
    ('昭和区', '昭和区'),
    ('中区', '中区'),
]

class SearchForm(forms.Form):
    selected_category = forms.ModelChoiceField(
        label='業態',
        required=False,
        queryset=Category.objects.all(),
    )
    freeword = forms.CharField(min_length=2, max_length=100, label='', required=False)
    
    region = forms.ChoiceField(
        label='地域',
        choices=REGION_CHOICES,
        required=False
    )

    price_range = forms.ChoiceField(
        label='価格帯',
        choices=PRICE_CHOICES,
        required=False
    )

    rating = forms.ChoiceField(
        label='評価',
        choices=SCORE_CHOICES,
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['selected_category'].widget.attrs.update({'class': 'form-control'})
        self.fields['freeword'].widget.attrs.update({'class': 'form-control', 'placeholder': 'フリーワード'})
        self.fields['region'].widget.attrs.update({'class': 'form-control'})
        self.fields['price_range'].widget.attrs.update({'class': 'form-control'})
        self.fields['rating'].widget.attrs.update({'class': 'form-control'})

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', max_length=254)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['score', 'comment']

# サブスクリプション登録
class SubscriptionForm(forms.Form):
    stripe_token = forms.CharField()

# 予約フォーム
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['date_time', 'num_people', 'shop']  # datetimeと人数を追加
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

# レビュー編集フォーム
class ReviewEditForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['score', 'comment']
        widgets = {
            'score': forms.RadioSelect(choices=SCORE_CHOICES),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

# プロフィール編集フォーム
class ProfileEditForm(UserChangeForm):
    password = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'postal_code', 'address', 
            'phone_number', 'birthday', 'job'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
