# Imports for CRUD views
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Org, Team
from .forms import OrgDetailForm, TeamDetailForm
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseForbidden

# configure Logger
import logging
logger = logging.getLogger(__name__)

def context(request):
    return render(request, 'Organization/org_context.html')


def teams_list(request):
    context = {
        'teams': Team.objects.all()   #TODO: This has to be org specific.
    }
    return render(request, 'Organization/teams_list.html', context)


# CRUD views for Org
class OrgDetailView(UpdateView):
    model = Org
    template_name = 'Organization/org-form.html'
    form_class = OrgDetailForm
    # TODO: Show the Join URL in the detail page.


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
        form.fields['allowed_email_domain'].widget.attrs ={'placeholder': 'Ex: @test.com'}
        return form


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
        orgObj = get_object_or_404(Org,pk=pk)
        # Validate join URL by checking if orgName given for orgID is correct.
        # This logic may need to be revised in future.
        if orgObj.org_name != OrgName: #case sensitive compare
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
class TeamDetailView(UpdateView):
    model = Team
    template_name = 'Organization/team-form.html'
    form_class = TeamDetailForm


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    template_name = 'Organization/team-form.html'
    fields = ['team_name', 'team_admins', 'org', 'sub_teams', 'team_members']

    def form_valid(self, form):
        return super().form_valid(form)


class TeamUpdateView(LoginRequiredMixin, UpdateView):
    model = Team
    template_name = 'Organization/team-form.html'
    fields = ['team_name', 'team_admins', 'org', 'sub_teams', 'team_members']

    def form_valid(self, form):
        return super().form_valid(form)


class TeamDeleteView(LoginRequiredMixin, DeleteView):
    model = Team
    template_name = 'Organization/team-confirm-delete.html'
    success_url = '/'
