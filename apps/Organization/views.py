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
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.mixins import UserPassesTestMixin
from apps.Users.middleware import get_current_org
from django.urls import reverse
from apps.Users.mixin import UserHasAccessToTeamMixin, UserCanModifyTeamMixin
from apps.Users.mixin import UserHasAccessToOrgMixin, UserCanDeleteOrgMixin
from django.utils.text import slugify
from django.http import HttpResponseForbidden

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
    template_name = 'Organization/org-create.html'
    fields = ['org_name', 'allowed_email_domain']
    context_object_name = "org"

    def get(self, request, *args, **kwargs):
        # During 'get' we ideally want to show an empty form to allow the user to
        # create and Org. However since we do not allow the user to be part of more
        # than one Org, we need to check and throw and error if the user is already
        # part of another Org. We do not allow the user to create an Org if he is already
        # part of another Org.
        cur_user = request.user
        if cur_user.org is not None:
            context = {'cur_org': cur_user.org}
            return render(request, 'Organization/org_error_second.html', context)

        # Not part of any Org. Show the empty form. Taken care of by CreateView
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # This is called if form is valid after Form submit.
        # Since there would be no users in the Org yet, we will mark the current user
        # as Admin and also add him to the Org.
        userObj = self.request.user

        # Set the user who is creating this Org as the admin of the Org created.
        orgObj = form.save(commit=False)
        orgObj.admin = userObj
        orgObj.save()

        # Add the user to the newly created Org.
        # Currently a user can only belong to a single org and so the relationship is
        # represented by a FK field. If in future when a user can belong to multiple orgs
        # the field could become a ManyToMany field. Modify the below addition accordingly
        userObj.org = orgObj
        userObj.save()

        # if a user is already part of any org, he should exit the org first.
        # Only then should he be allowed to create a new Org.
        # Not only that, he should unsubscribe from all teams he is part of it.

        context = {'org': orgObj}
        return render(self.request, 'Organization/org-creation-success.html', context)

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


class OrgUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Org
    template_name = 'Organization/org-form.html'
    fields = ['org_name', 'admin', 'allowed_email_domain']

    def form_valid(self, form):
        return super().form_valid(form)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        form = super(OrgUpdateView, self).get_form(form_class)
        form.fields['allowed_email_domain'].widget.attrs = {'placeholder': 'Ex: @trackzilla.com'}
        org_obj = self.get_object()
        # List should contain only users of that Org.
        form.fields['admin'].queryset = org_obj.user_set.all()
        return form

    # Only the admin of the Org should be able to access this page.
    # Implementing the function called by UserPassesTestMixin.
    def test_func(self):
        orgObj = self.get_object()
        curUser = self.request.user
        if orgObj.admin == curUser:
            logger.debug("User %s admin of Org %s. Allowed to access Org Update page" %
                (curUser.get_email(), orgObj.get_name()))
            return True
        else:
            logger.debug("User %s Not admin of Org %s. Denied access to Org Update page" %
                (curUser.get_email(), orgObj.get_name()))
            return False


class OrgDeleteView(LoginRequiredMixin, UserCanDeleteOrgMixin, View):
    def get(self, request, pk):
        orgObject = get_object_or_404(Org, id=pk)
        cur_user = request.user

        # Check if the user is the admin of the Org to delete it.
        # Ideally this check can never be true because UserCanDeleteOrgMixin ensures
        # the user is the admin of the Org.
        if cur_user != orgObject.admin:
            logger.error("UserCanDeleteOrgMixin has not done its job. user:%s org:%s org_admin:%s",
                cur_user.get_email(), orgObject.get_name(), orgObject.admin.get_email())
            return HttpResponseForbidden('You cannot delete an Org you do not manage')

        # An Org admin cannot delete an Org if:
        # 1) Org has any teams. All the teams should be deleted.
        # 2) Org has any Resources. All the resources should be deleted.
        # 3) Org has any Users. All the users need to exit the Org.
        # Only if the Org doesnot satisfy any of the above cases, should it be allowed
        # to be deleted.
        # NOTE: However there is one corner case where there is only one user in
        # the org and that is the org admin. Since he cannot re-assin the admin role
        # to someone else, he would not be allowed to exit the Org. In such case, the 
        # only option is to allow deletion of the Org. we should manually remove the admin
        # and allow deletion.

        team_list = orgObject.team_set.all()
        res_list = orgObject.resource_set.all()
        # We need to show all users other than the org admin. As the admin once removed
        # cannot delete the org.
        user_list = orgObject.user_set.exclude(id=cur_user.id)

        # Check if there are teams and resources still part of the Org.
        # In case of users, we should not have any other user other than the Org admin.
        if len(team_list) > 0 or len(res_list) > 0 or len(user_list) > 0:
            # Show the user, the list of actions he has to take.
            context = {'res_list': res_list, 'team_list': team_list,
                       'user_list': user_list,
                       'del_org': orgObject}
            return render(request, 'Organization/org_del_criteria.html', context=context)
        else:
            # Exit criteria met. show a confirm exit page.
            context = {'del_org': orgObject}
            return render(request, 'Organization/org-confirm-delete.html', context=context)

    def post(self, request, pk):
        orgObject = get_object_or_404(Org, id=pk)
        cur_user = request.user

        # Check if the user meets the exit criteria. This should ideally be shown
        # when the user does a GET. But in case we have users who do a direct POST
        # using some tools then we should not allow it.
        # The below condition catches those cases and prevents accidental exit.
        team_list = orgObject.team_set.all()
        res_list = orgObject.resource_set.all()
        user_list = orgObject.user_set.all()

        # Check if there are teams and resources still part of the Org.
        # In case of users, we should not have any other user other than the Org admin.
        if len(team_list) > 0 or len(res_list) > 0 or len(user_list) > 1:
            return HttpResponseRedirect(reverse('Org:org-delete',
                                                kwargs={'pk': orgObject.pk}))

        # Criteria met. Lets exit from the Org and then delete it.
        orgObject.user_set.remove(cur_user)
        orgObject.admin = None
        orgObject.delete()
        # redirect to Home Page.
        return HttpResponseRedirect(reverse('home'))


class OrgExitView(LoginRequiredMixin, UserHasAccessToOrgMixin, View):
    def get(self, request, pk):
        orgObject = get_object_or_404(Org, id=pk)
        cur_user = request.user

        # Check if the user even belongs to the Org to exit it.
        # Ideally this check can never be true because UserHasAccessToOrgMixin ensures
        # the user is part of the Org.
        if cur_user not in orgObject.user_set.all():
            return HttpResponseForbidden('You cannot exit an Org you do not belong to')

        # A user should not be allowed to exit the Org if:
        # 1) User has any resources in his name. They should be reassigned.
        # 2) User is the admin of any resources. Some one else should be made admin.
        # 3) User is the admin of any team. Some one else should be made admin.
        # 4) User is the member of any team. User should exit the teams.
        # 5) User is the admin of the Org. Someone else should be made admin.
        # Only if the user doesnot satisfy any of the above cases, should he be allowed
        # to exit the Org.

        res_list = cur_user.res_being_used.all()
        res_admin_list = cur_user.res_being_managed.all()
        team_list = cur_user.team_member_of.all()
        team_admin_list = cur_user.team_admin_for.all()
        org_admin_list = cur_user.admin_for_org.all()

        # Check if even one of the above lists has any values.
        if len(res_list) > 0 or len(res_admin_list) > 0 or len(team_list) > 0 or \
           len(team_admin_list) > 0 or len(org_admin_list) > 0:
            # Show the user, the list of actions he has to take.
            context = {'res_list': res_list, 'res_admin_list': res_admin_list,
                       'team_list': team_list, 'team_admin_list': team_admin_list,
                       'org_admin_list': org_admin_list,
                       'exit_org': orgObject}
            return render(request, 'Organization/org_exit_criteria.html', context=context)
        else:
            # Exit criteria met. show a confirm exit page.
            context = {'exit_org': orgObject}
            return render(request, 'Organization/org-confirm-exit.html', context=context)

    def post(self, request, pk):
        orgObject = get_object_or_404(Org, id=pk)
        cur_user = request.user

        # Check if the user meets the exit criteria. This should ideally be shown
        # when the user does a GET. But in case we have users who do a direct POST
        # using some tools then we should not allow it.
        # The below condition catches those cases and prevents accidental exit.
        res_list = cur_user.res_being_used.all()
        res_admin_list = cur_user.res_being_managed.all()
        team_list = cur_user.team_member_of.all()
        team_admin_list = cur_user.team_admin_for.all()
        org_admin_list = cur_user.admin_for_org.all()

        # Check if even one of the above lists has any values.
        if len(res_list) > 0 or len(res_admin_list) > 0 or len(team_list) > 0 or \
           len(team_admin_list) > 0 or len(org_admin_list) > 0:
            return HttpResponseRedirect(reverse('Org:org-exit',
                                                kwargs={'pk': orgObject.pk}))

        # Criteria met. Lets exit from the Org.
        orgObject.user_set.remove(cur_user)
        # redirect to Home Page.
        return HttpResponseRedirect(reverse('home'))


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
                (loggedInUser.name, loggedInUser.org.org_name))  # TODO: Change to template.
        elif loggedInUser.org is not None and loggedInUser.org == orgObj:
            return HttpResponse("User %s already part of org %s" %
                (loggedInUser.name, loggedInUser.org.org_name))  # TODO: Change to template.
        else:  # User part of a different Org. As of now only one Org allowed.
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


class TeamExitView(LoginRequiredMixin, UserHasAccessToTeamMixin, View):
    def get(self, request, pk):
        teamObj = get_object_or_404(Team, id=pk)
        cur_user = request.user
        # Only a user who belongs to the team can exit it. Check if the logged in user
        # visiting the Url belongs to the team
        # Note that we could have a team_admin who is not part of the team.
        # For a team_admin to exit, the admin has to choose another admin and remove
        # himself from the admin list.
        if cur_user not in teamObj.team_members.all():
            return HttpResponseForbidden('You cannot exit a team you do not belong to')
            # TODO: Show a template describing the error. Currently it shows up as a string.

        # remove the user from the team.
        # TODO: Have a confirm-exit template process than a direct exit.
        teamObj.team_members.remove(cur_user)

        context = {'teamObj': teamObj}
        return render(request, 'Organization/team-exit-success.html', context=context)

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
