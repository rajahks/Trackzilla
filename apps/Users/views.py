from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserDetailForm
# Imports for CRUD views
from .models import AssetUser
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin


def home(request):
    return render(request, 'Users/home.html')


def people_list(request):
    context = {
        'people': AssetUser.objects.all()
    }
    return render(request, 'Users/people_list.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Your account has been successfully created. You can now login!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'Users/register.html', {'form': form})


class UserDetailView(UpdateView):
    model = AssetUser
    template_name = 'Users/user-form.html'
    form_class = UserDetailForm


class UserCreateView(LoginRequiredMixin, CreateView):
    model = AssetUser
    # This CBV expects a template named user_form.html. Overriding.
    template_name = 'Users/user-form.html'
    fields = ['username', 'email', 'password', 'org_id']

    def form_valid(self, form):
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = AssetUser
    template_name = 'Users/user-form.html'
    fields = ['username', 'email', 'org_id']

    def form_valid(self, form):
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = AssetUser
    template_name = 'Users/user-confirm-delete.html'
    success_url = '/'
