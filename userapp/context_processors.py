from .models import Category

def common(request):
    """テンプレートに毎回渡すデータ"""
    context = {
        'category_list': Category.objects.all().order_by('category_l'),
    }

    return context
