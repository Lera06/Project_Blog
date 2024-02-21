from django.urls import path, re_path
from .views import home, about, post_share, post_comment, post_search
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    UserPostListView,
    TagListView,
    )


urlpatterns = [
    # path('', home, name='blog-home'),
    path('', PostListView.as_view(), name='blog-home'),
    path('user/<str:username>', UserPostListView.as_view(), name='user-posts'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('post/new/', PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('about/', about, name='blog-about'),

    path('post/<int:post_id>/share/', post_share, name='post-share'),
    path('<int:post_id>/comment/', post_comment, name='post-comment'),
    re_path(r'^tag/(?P<slug>[-\w]+)/$', TagListView.as_view(), name='tagged-posts'),
    path('search/', post_search, name='post-search'),

    ]
