from django import template
from django.db.models import Count
from ..models import Post


# register используется для регистрации шаблонных тегов приложения
register = template.Library()


# Создание тега, который возвращает общее число постов, в виде строки
@register.simple_tag
def total_posts():
    return Post.objects.count()


# Зарегистрировали шаблонный тег и указали шаблон, который будет прорисовываться возвращенными значениями
# Тег включения всегда возвращает словарь
@register.inclusion_tag('blog/latest_posts.html')
def show_latest_posts(count=5):
    latest_posts = Post.objects.order_by('-date_posted')[:count]
    return {'latest_posts': latest_posts}


# Создание тега, чтобы отображать посты с наибольшим числом комментариев
@ register.simple_tag()
def get_most_commented_posts(count=3):
    return Post.objects.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]

