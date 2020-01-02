# Imports for CRUD views
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
)
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Org, Team
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.forms.widgets import CheckboxSelectMultiple
from apps.Users.middleware import get_current_org
from django.urls import reverse
from apps.Users.mixin import UserHasAccessToTeamMixin, UserCanModifyTeamMixin
from apps.Users.mixin import UserHasAccessToOrgMixin
from django.utils.text import slugify

# configure Logger
import logging
logger = logging.getLogger(__name__)

def teams_list(request):
    context = {
        'teams': Team.objects.all()   #TODO: This has to be org specific.
    }
    return render(request, 'Organization/teams_list.html', context)


# CRUD views for Org

# TODO: We need to have something like HasPermissionMixin to even check if the user has
# permission to access a view. In our case, only a user belonging to the Org should be able
# to view details.

class OrgDetailView(LoginRequiredMixin, UserHasAccessToOrgMixin, View):
    def get(self, request, pk):
        orgObject = get_object_or_404(Org, id=pk)
        context = {'Org': orgObject}
        return render(request, 'Organization/org_context.html', context=context)


class OrgCreateView(LoginRequiredMixin, CreateView):
    model = Org
    template_name = 'Organization/org-form.html'
    fields = ['org_name', 'admin', 'allowed_email_domain']

    def form_valid(self, form):
        return super().form_valid(form)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        form = super(OrgCreateView, self).get_form(form_class)
        form.fields['allowed_email_domain'].widget.attrs = {'placeholder': 'Ex: @trackzilla.com'}
        return form
# TODO: Creating new Org with name having spaces fails as getting the join link of that fails.
# Getting join list fails as it expects name to be a slug but this may not be the case.

# TODO: When a user creates an Org, he should be set as the admin of the org and the FK value
# in the User object should be updated on save. This leads to another problem where a User
# could create multiple orgs. This would mean it should be ManyToManyField 


class OrgUpdateView(LoginRequiredMixin, UpdateView):
    model = Org
    template_name = 'Organization/org-form.html'
    fields = ['org_name', 'admin', 'allowed_email_domain']

    def form_valid(self, form):
        return super().form_valid(form)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        form = super(OrgUpdateView, self).get_form(form_class)
        form.fields['allowed_email_domain'].widget.attrs ={'placeholder': 'Ex: @test.com'}
        return form


class OrgDeleteView(LoginRequiredMixin, DeleteView):
    model = Org
    template_name = 'Organization/org-confirm-delete.html'
    success_url = '/'


@login_required
def OrgJoinView(request, pk, OrgName, *args, **kwargs):
    """View which handles the join url. The org details will be extracted from the url
    and the logged in user will be added to the same.
    Before adding the user, the url is validated. Currently this is a simple check to see
    if the orgName corresponds to the org id. In future the Org join link could have a 
    hashed component so that guessing the join url is made difficult.

    TODO: Our usercase for join-url is that when a new user clicks on the join link,
    he should be allowed to sign-up if he doesn't have an account and then once user
    signs-in should be added to the org. So this would mean, join-url redirects to Sign-in,
    if user has to create an account he clicks on the Sign-up link. Post Sign-up he should
    be redirected to the join-url. Not sure how to attach the 'next' url to the sign-up
    button dynamically. So until that is figured out we will have a 2 step process.
    Step 1: User has to create an account first
    Step 2: Click on the join Url. User will be added to Org. Asked to login if required.
    We also need to consider what happens in case of SSO and tweak this further.

    Arguments:
        request {HttpRequest} -- The standard request object provided by Django
        pk {int} -- Primary key of the org extracted from the Url
        OrgName {slug} -- Slug field(str) extracted from the url

    Raises:
        Http404: When the join url is invalid.

    Returns:
        HttpResponse -- Standard Django response
    """
    if request.method == 'GET':
        # Fetch the organization based on pk.
        orgObj = get_object_or_404(Org, pk=pk)
        # Validate join URL by checking if orgName given for orgID is correct.
        # This logic may need to be revised in future.

        # Since org name can have spaces, we currently return a slugyfied version of the
        # org name in join link. Convert org name and Compare with what was passed.
        if slugify(orgObj.org_name) != OrgName:
            raise Http404("Invalid Join URL. No such organization exists")

        # Fetch the logged in User
        loggedInUser = request.user

        # TODO: Add email validation logic here i.e. the admin of the Org should be allowed
        # to specify rules such as only email ids of particular domain can join this org.
        # Eg: @abc.com
        # This way we will prevent random ppl from joining the org even when the link leaks
        # outside an Org.
        if not orgObj.is_email_allowed(loggedInUser.email):
            logger.error("User %s was NOT allowed to join Org %s."%(loggedInUser.get_email(),OrgName))
            return HttpResponseForbidden("You do not have permission to join this Organization")

        if loggedInUser.org is None:
            # User not part of any Org. Add to the Org.
            # TODO: Should we have a workflow where the admin has to confirm and only then
            # they will be added to the Org.
            loggedInUser.org = orgObj
            loggedInUser.save()
            logger.info("User %s added to Org %s" %(loggedInUser.email, OrgName))
            # TODO: Send an email or notify the admin that a new user has been added.
            return HttpResponse("User %s added to org %s" %
                (loggedInUser.name, loggedInUser.org.org_name)) #TODO: Change to template.
        elif loggedInUser.org is not None and loggedInUser.org == orgObj:
            return HttpResponse("User %s already part of org %s" %
                (loggedInUser.name, loggedInUser.org.org_name)) #TODO: Change to template.
        else: # User part of a different Org. As of now only one Org allowed.
            return HttpResponse("User %s already part of a different Org %s. Exit that org to join a new one." %
                (loggedInUser.name, loggedInUser.org.org_name))


# CRUD views for team
class TeamDetailView(LoginRequiredMixin, UserHasAccessToTeamMixin, View):
    def get(self, request, pk):
        teamObj = get_object_or_404(Team, id=pk)
        context = {'teamObj': teamObj}
        return render(request, 'Organization/team_detail.html', context=context)

    # Other generic views have an included get_object function which returns the current
    # object. As 'View' base class does not have this, we need to implement it as it is
    # required by UserHasAccessToTeamMixin to fetch the current object.
    def get_object(self):
        if 'pk' not in self.kwargs.keys():
            logger.error("pk not present. Cannot fetch Team. Denying access by returning None")
            return None

        # Fetch the object.
        obj = get_object_or_404(Team, pk=self.kwargs['pk'])
        return obj


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    template_name = 'Organization/team-new.html'
    fields = ['team_name', 'team_admins', 'parent_team', 'team_members']

    def get_form(self):
        form = super(TeamCreateView, self).get_form()
        cur_user_org = get_current_org()
        # form.fields['team_members'].widget = CheckboxSelectMultiple()
        form.fields['team_members'].queryset = cur_user_org.user_set.all()
        # form.fields['team_admins'].widget = CheckboxSelectMultiple()
        form.fields['team_admins'].queryset = cur_user_org.user_set.all()
        # exclude the current team from this list
        form.fields['parent_team'].queryset = cur_user_org.team_set.all()
        return form

    def form_valid(self, form):
        # Set the org to current user's org
        form.instance.org = get_current_org()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('Org:team-detail', kwargs={'pk': self.object.pk } )

    def get_context_data(self, **kwargs):
        ctx = super(TeamCreateView, self).get_context_data(**kwargs)
        ctx['org'] = get_current_org()  # form would already be added
        return ctx


class TeamUpdateView(LoginRequiredMixin, UserCanModifyTeamMixin, UpdateView):
    model = Team
    template_name = 'Organization/team-update.html'
    fields = ['team_name', 'team_admins', 'parent_team', 'team_members']
    context_object_name = 'team'  # team obj passed to the template

    def get_form(self):
        form = super(TeamUpdateView, self).get_form()
        cur_user_org = get_current_org()
        team_obj = self.get_object()
        # form.fields['team_members'].widget = CheckboxSelectMultiple()
        form.fields['team_members'].queryset = cur_user_org.user_set.all()
        # form.fields['team_admins'].widget = CheckboxSelectMultiple()
        form.fields['team_admins'].queryset = cur_user_org.user_set.all()
        # exclude the current team from this list
        # TODO: Extend this to exclude all child teams(including grand child teams) as well.
        form.fields['parent_team'].queryset = cur_user_org.team_set.exclude(id=team_obj.id)
        return form

    def form_valid(self, form):
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super(TeamUpdateView, self).get_context_data(**kwargs)
        ctx['org'] = get_current_org()  # form would already be added
        return ctx

    def get_success_url(self):
        return reverse('Org:team-detail', kwargs={'pk': self.object.pk})


class TeamDeleteView(LoginRequiredMixin, UserCanModifyTeamMixin, DeleteView):
    model = Team
    template_name = 'Organization/team-confirm-delete.html'
    success_url = '/'
    context_object_name = 'team'
