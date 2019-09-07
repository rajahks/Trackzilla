# Imports for CRUD views
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Org, Team
from .forms import OrgDetailForm, TeamDetailForm
from django.shortcuts import render


def context(request):
    return render(request, 'Organization/org_context.html')


def teams_list(request):
    context = {
        'teams': Team.objects.all()
    }
    return render(request, 'Organization/teams_list.html', context)


# CRUD views for Org
class OrgDetailView(UpdateView):
    model = Org
    template_name = 'Organization/org-form.html'
    form_class = OrgDetailForm


class OrgCreateView(LoginRequiredMixin, CreateView):
    model = Org
    template_name = 'Organization/org-form.html'
    fields = ['org_name', 'admin_id']

    def form_valid(self, form):
        return super().form_valid(form)


class OrgUpdateView(LoginRequiredMixin, UpdateView):
    model = Org
    template_name = 'Organization/org-form.html'
    fields = ['org_name', 'admin_id']

    def form_valid(self, form):
        return super().form_valid(form)


class OrgDeleteView(LoginRequiredMixin, DeleteView):
    model = Org
    template_name = 'Organization/org-confirm-delete.html'
    success_url = '/'


# CRUD views for team
class TeamDetailView(UpdateView):
    model = Team
    template_name = 'Organization/team-form.html'
    form_class = TeamDetailForm


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    template_name = 'Organization/team-form.html'
    fields = ['team_name', 'team_admins', 'org_id', 'sub_teams', 'team_members']

    def form_valid(self, form):
        return super().form_valid(form)


class TeamUpdateView(LoginRequiredMixin, UpdateView):
    model = Team
    template_name = 'Organization/team-form.html'
    fields = ['team_name', 'team_admins', 'org_id', 'sub_teams', 'team_members']

    def form_valid(self, form):
        return super().form_valid(form)


class TeamDeleteView(LoginRequiredMixin, DeleteView):
    model = Team
    template_name = 'Organization/team-confirm-delete.html'
    success_url = '/'
