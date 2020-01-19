from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserDetailForm
# Imports for CRUD views
from django.contrib.auth import get_user_model
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from apps.Resource.models import Resource
from .middleware import get_current_org
from .mixin import UserHasAccessToViewUserMixin, UserCanDelUserMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import UserPassesTestMixin

import logging
logger = logging.getLogger(__name__)

# Fetch the current configured User model.
User = get_user_model()


@login_required
def home(request):
    """Users  landing page

    Arguments:
        request {[type]} -- [description]

    Returns:
        [type] -- [description]
    """

    # A user could belong to multiple Orgs. We need to restrict all the information based
    # on an org. When a user first logs in, show the first org in the list.
    # Once he selects it, save the value in a thread local variable. Change this variable
    # when the user selects a different Org from the Org context dropdown

    # The current org is saved in thread local variable called CURRENT_ORG.
    cur_org = get_current_org()
    logger.debug("Displaying home page for Org:%s User:%s" %
                 (cur_org, request.user))

    # First filter all the resources based on the current chosen Org
    resources_in_org = Resource.objects.filter(org=cur_org)

    # Right pane - block 1 - Resources needing action. We need to fetch the list of devices
    # which the users needs to ack or deny
    # Send this as a list as part of dict
    needActionList = []
    resNeedActionQset = resources_in_org.filter(current_user__id=request.user.id).filter(status=Resource.RES_ASSIGNED)
    for res in resNeedActionQset:
        needActEntryDict = {}
        needActEntryDict['name'] = res.name
        needActEntryDict['ack_url'] = request.build_absolute_uri(res.get_acknowledge_url())
        needActEntryDict['deny_url'] = request.build_absolute_uri(res.get_deny_url())
        needActEntryDict['detail_url'] = request.build_absolute_uri(res.get_absolute_url())
        needActionList.append(needActEntryDict)

    # Right pane - block 2 - Resources in disputed state.
    # We need to fetch the list of devices which the user has deny
    # Send this as a list as part of dict
    resInDisputeList = []
    resDisputeQset = resources_in_org.filter(current_user__id=request.user.id).filter(
                                             status=Resource.RES_DISPUTE)
    for res in resDisputeQset:
        disputeEntryDict = {}
        disputeEntryDict['name'] = res.get_name()
        disputeEntryDict['ack_url'] = request.build_absolute_uri(res.get_acknowledge_url())
        disputeEntryDict['detail_url'] = request.build_absolute_uri(res.get_absolute_url())
        resInDisputeList.append(disputeEntryDict)

    # Right Pane - block 3 - Resources in your name and acknowledged
    inUseList = []
    resInUseQset = resources_in_org.filter(current_user__id=request.user.id).filter(status=Resource.RES_ACKNOWLEDGED)
    for res in resInUseQset:
        inUseEntryDict = {}
        inUseEntryDict['name'] = res.get_name()
        inUseEntryDict['update_url'] = request.build_absolute_uri(res.get_update_url())
        inUseEntryDict['detail_url'] = request.build_absolute_uri(res.get_absolute_url())
        inUseList.append(inUseEntryDict)

    # Resources in you teams of the current Org.
    # Since user could be part of more than 1 team, we need to fetch all the teams he is part of
    teamResourceDict = {}  # List of resource objects in the team
    try:
        logged_in_user = User.objects.get(id=request.user.id)
        team_list = logged_in_user.team_member_of.filter(org=cur_org)  # Filter based on currently selected Org.
        for team in team_list:
            teamResourceList = []
            # Find out all the members of the team
            members = team.team_members.filter(org=cur_org)
            # Now for each member we need to find all the resources he owns and
            # then add it to the list
            for member in members:  #TODO: Should we exclude the current user here?
                teamResourceList += member.res_being_used.filter(org=cur_org)

            # Add the team resource list against the team name in teamResourceDict
            teamResourceDict[team.team_name] = teamResourceList
    except User.DoesNotExist:
        # The call User.objects.get can fail for root user created from command line
        # as it will not be part of the User table. Log the error as of now
        # TODO: Catch the right error and come up with a better way
        logger.error("User.objects.get call failed for user %s id%d" % (request.user.get_username(), request.user.id))

    # Resources you are managing
    resBeingManagedList = resources_in_org.filter(device_admin__id=request.user.id)

    context = {"needActionList": needActionList,
               "resInDisputeList": resInDisputeList,
               "inUseList": inUseList,
               "teamResourceDict": teamResourceDict,
               "managedDeviceList": resBeingManagedList, }

    return render(request, 'Users/home.html', context=context)


#TODO: Hackfest Addition. Not sure why this was added. This maynot be required.
def people_list(request):
    context = {
        'people': User.objects.all()   #TODO: Needs to be ORG specific.
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


class UserDetailView(LoginRequiredMixin, UserHasAccessToViewUserMixin,
                     DetailView):
    model = get_user_model()
    template_name = 'Users/user_detail.html'
    # form_class = UserDetailForm
    context_object_name = 'user_obj'    # The user we are viewing.
                                        # The other user would be logged in user.

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_obj = self.get_object()

        # A user will have resources he is using and also resources he would be
        # managing. He could also be using the resource he is managing.
        # Rather than showing these in separate tabs, we will display both of this info
        # in a single tab and show the role. Role will have 'User' or 'Admin' or both
        # 'User' and 'Admin' if he is using a resource he is managing.
        # Since forming this data is easier here compared to a template, we form it and
        # add it to the context.
        # The information is sent as a dict with entries as follows
        # {
        #     '<pk of res (integer) >': { 'res_obj': <resource object>,
        #                                 'role_list': [ 'User', 'Admin']
        #                               }
        # }

        res_dict = {}
        for res in user_obj.res_being_used.all():
            res_dict[res.pk] = {'res_obj': res, 'role_list': ['User']}

        for res in user_obj.res_being_managed.all():
            if res.pk in res_dict.keys():
                # Dict entry already present
                res_dict[res.pk]['role_list'].append('Admin')
            else:
                # Dict entry no present. Create a new one
                res_dict[res.pk] = {'res_obj': res, 'role_list': ['Admin']}

        ctx['res_dict'] = res_dict

        # Similar to resources above, create a teams-roles dict.
        teams_dict = {}
        for team in user_obj.team_member_of.all():
            teams_dict[team.pk] = {'team_obj': team, 'role_list': ['Member']}

        for team in user_obj.team_admin_for.all():
            if team.pk in teams_dict.keys():
                # Dict entry already present
                teams_dict[team.pk]['role_list'].append('Admin')
            else:
                # Dict entry no present. Create a new one
                teams_dict[team.pk] = {'team_obj': team, 'role_list': ['Admin']}

        ctx['teams_dict'] = teams_dict

        return ctx


# TODO: Is the create view required? Also the password set through this is not
# getting hashed. Evaluate what changes are required for this.
# TODO: Not exposing this for now. A user will need to signup.
class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    # This CBV expects a template named user_form.html. Overriding.
    template_name = 'Users/user-form.html'
    fields = ['name', 'email', 'password', 'org']

    def form_valid(self, form):
        return super().form_valid(form)


# TODO: Should be allow the user to update the password from this view?
# Added a different view to change password. From that view both admin and the user can
# change the password. Will not be exposing this update view as of now.
class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'Users/user-form.html'
    fields = ['name']

    def get_form(self):
        form = super(UserUpdateView, self).get_form()
        return form

    def form_valid(self, form):
        return super().form_valid(form)


class UserDeleteViewOld(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'Users/user-confirm-delete.html'
    success_url = '/'


class UserDeleteView(LoginRequiredMixin, UserCanDelUserMixin, View):
    def get(self, request, pk):
        user_obj = get_object_or_404(User, id=pk)

        # An Org admin cannot delete a user if:
        # 1) User part of any teams. User should be removed from all teams.
        # 2) User managed any teams. Someone else should be made admin or team should
        #    be deleted.
        # 3) User has any Resources. All the resources should be reassigned or deleted.
        # 4)User manages any resources. Someone else should be made admin or resource
        #    should be deleted.
        # 5) User is the admin of the Org - Only an admin can delete users but an admin
        #    cannot delete himself.
        # Only if the user object doesnot satisfy any of the above cases,
        # should it be allowed to be deleted.
        # NOTE: However there is one corner case where there is only one user in
        # the org and that is the org admin. Since he cannot re-assin the admin role
        # to someone else, he would not be allowed to exit the Org. In such case, the
        # only option is to allow deletion of the Org. we should manually remove the admin
        # and allow deletion.

        team_list = user_obj.team_member_of.all()  # Teams part of
        team_admin_list = user_obj.team_admin_for.all()  # Admin for teams
        res_list = user_obj.res_being_used.all()  # resources being used.
        res_admin_list = user_obj.res_being_managed.all()  # Resource being managed.
        org_admin_list = user_obj.admin_for_org.all()  # Admin for Orgs

        # TODO: org_admin_list needs a bit of fix up. Firstly only an org admin can access
        # the delete user page. So what should we do when the admin tries to delete
        # himself? Currently we should it in the action list that he org admin has to be
        # reassigned. The org admin has to be changed and the new admin has to now delete
        # the old admin's account. Needs a better scheme.

        # Check if there are teams and resources in the User's name.
        # Show the list to admin along with the action to be taken.
        if (len(team_list) > 0 or len(team_admin_list) > 0 or
                len(res_list) > 0 or len(res_admin_list) > 0) or len(org_admin_list) > 0:
            # Show the user, the list of actions he has to take.
            context = {'res_list': res_list, 'team_list': team_list,
                       'team_admin_list': team_admin_list,
                       'res_admin_list': res_admin_list,
                       'org_admin_list': org_admin_list, 'del_user': user_obj}
            return render(request, 'Users/user_del_criteria.html', context=context)
        else:
            # Del criteria met. show a confirm delete page.
            context = {'del_user': user_obj}
            return render(request, 'Users/user-confirm-delete.html', context=context)

    def post(self, request, pk):
        user_obj = get_object_or_404(User, id=pk)

        # Check if the user meets the del criteria. This should ideally be shown
        # when the user does a GET. But in case we have users who do a direct POST
        # using some tools then we should not allow it.
        # The below condition catches those cases and prevents accidental delete.

        team_list = user_obj.team_member_of.all()  # Teams part of
        team_admin_list = user_obj.team_admin_for.all()  # Admin for teams
        res_list = user_obj.res_being_used.all()  # resources being used.
        res_admin_list = user_obj.res_being_managed.all()  # Resource being managed.
        org_admin_list = user_obj.admin_for_org.all()  # Admin for Orgs

        # Check if there are teams and resources in the User's name.
        # Show the exit_
        if (len(team_list) > 0 or len(team_admin_list) > 0 or
                len(res_list) > 0 or len(res_admin_list) > 0) or len(org_admin_list) > 0:
            return HttpResponseRedirect(reverse('user-delete',
                                                kwargs={'pk': user_obj.pk}))

        # Criteria met. Lets delete the user.
        user_obj.delete()
        # redirect to Home Page.
        return HttpResponseRedirect(reverse('home'))


class ChangePasswordView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ Using this view, the user can change his password. Since a user has to login to
    access this view and until we have a Forgot password flow, we will allow the Org admin
    to access this view and change the password.
    In summary, the user and the org admin can change the password of the user.
    TODO: Revise this workflow in future.
    Also since we are allowing the admin to change the password, we are using the
    SetPasswordForm instead of PasswordResetForm which asks for the current password.
    """

    def get(self, request, *args, pk, **kwargs):
        user = self.get_object()
        form = SetPasswordForm(user)
        return render(request, 'Users/change_password.html', {'form': form})

    def get_object(self):
        if 'pk' not in self.kwargs.keys():
            logger.error("pk not present. Cannot fetch User object. Returning None")
            return None

        return get_object_or_404(User, id=self.kwargs['pk'])

    def post(self, request, *args, pk, **kwargs):
        user = self.get_object()
        form = SetPasswordForm(user, request.POST)  # TODO: Change to PasswordChangeForm when user whats to change.
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Password was successfully updated!')
            return redirect('change-password', pk)
        else:
            messages.error(request, 'Please correct the error below.')
            return render(request, 'Users/change_password.html', {'form': form})

    def test_func(self):
        user = self.get_object()
        # Only 2 people should be allowed to change password the user and the org admin if
        # the user belongs to an Org.
        # TODO: Move this to a separate Mixin in future.
        if self.request.user == user:
            logger.debug("User %s given access to change-password of self" %
                         user.get_name())
            return True
        elif user.org is not None and user.org.admin == self.request.user:
            logger.debug("Admin %s(%s) given access to change-password of user belonging"
                         " to same org" % (user.org.admin.get_name(), user.org.get_name())
                         )
            return True
        else:
            logger.debug("User %s(%s) denied access to change-password of %s(%s)" % (
                         self.request.user.get_name(), self.request.user.org,
                         user.get_name(), user.org))
            return False
