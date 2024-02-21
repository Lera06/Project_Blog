from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity


# posts = [
#     {'author': 'Bob Smith',
#      'title': 'Blog Post 1',
#      'content': 'First post content',
#      'date_posted': 'February 10, 2024'
#      },
#     {'author': 'Alice Doe',
#      'title': 'Blog Post 2',
#      'content': 'Second post content',
#      'date_posted': 'February 12, 2024'
#      },
#
# ]


def home(request):
    context = {
        'posts': Post.objects.all()
    }                      # 'posts' -> HTML, posts -> our created list posts
    return render(request, 'blog/home.html', context)


class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'       # <app>/<model>_<viewtpe>.html    --> blog/post_list.html
    context_object_name = 'posts'
    ordering = ['-date_posted']            # from the latest post to the oldest ones
    paginate_by = 3


class TagListView(ListView):
    # The TagListView will only return those where the tag contains some input slug.
    # That slug will come from the keyword arguments in the URL.
    # The listing for tagged posts:
    template_name = "blog/home.html"
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(tags__slug=self.kwargs.get("slug")).all()

    def get_context_data(self, *args,  **kwargs):
        context = super(TagListView, self).get_context_data(*args, **kwargs)
        context["tag"] = self.kwargs.get("slug")

        return context


# To see all the posts of a particular user:
class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 4

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))

        return Post.objects.filter(author=user).order_by('-date_posted')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'

    def get_similar_posts(self, post):
        post_tags_id = post.tags.values_list('id', flat=True)
        similar_posts = Post.objects.filter(tags__in=post_tags_id).exclude(id=post.id)
        similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags')[:3]
        return similar_posts

    def get_context_data(self, *args, **kwargs):
        # Метод get_context_data создает контекст шаблона, который включает post,
        # форму создания комментария и список похожих posts, полученных из get_similar_posts()
        context = super(PostDetailView, self).get_context_data(*args, **kwargs)
        context['post'] = self.get_object()
        context['form'] = CommentForm()
        context['comments'] = self.get_object().comments.all()

        context['similar_posts'] = self.get_similar_posts(self.object)

        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content']

    # To set an author of the post:
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()

        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()

        if self.request.user == post.author:
            return True
        return False


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})


def post_share(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id)

    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)

        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read '{post.title}'"
            message = f"Read {post.title} at {post_url}\n\n{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'valeriyamekhonina@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()

    return render(request, 'blog/share.html', {'post': post, 'form': form, 'sent': sent})


@login_required
@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    comment = None

    # A comment was posted
    form = CommentForm(request.POST)
    if form.is_valid():
        # Create a Comment object without saving it to the database
        comment = form.save(commit=False)
        # Assign the post to the comment
        comment.post = post
        # Save the comment to the database
        comment.save()

    return render(request, 'blog/comment.html',
                           {'post': post,
                            'form': form,
                            'comment': comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)

        if form.is_valid():
            query = form.cleaned_data['query']

            # Простой поиск:
            # results = Post.objects.annotate(
            #     search=SearchVector('title', 'content'),
            # ).filter(search=query)

            # Выделение основы слова:
            # SearchVector и SearchQuery
            # можно настроить под выделения основ слов и удаления стоп-слов на любом языке (config='spanish')
            search_vector = SearchVector('title', 'content', config='russian')
            search_query = SearchQuery(query, config='russian')

            results = Post.objects.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query),
                ).filter(search=search_query).order_by('-rank')

    return render(request, 'blog/search.html', {'form': form,
                                                'query': query,
                                                'results': results})