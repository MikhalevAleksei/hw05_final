from django.contrib.auth import logout
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


def logout_view(request):
    """Выход по GET-ссылке: LogoutView с Django 5.0 принимает только POST."""
    logout(request)
    return render(request, 'users/logged_out.html')
