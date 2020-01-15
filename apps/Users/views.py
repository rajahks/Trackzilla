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
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from apps.Resource.models import Resource
from .middleware import get_current_org
from .mixin import UserHasAccessToViewUserMixin

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
class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    # This CBV expects a template named user_form.html. Overriding.
    template_name = 'Users/user-form.html'
    fields = ['name', 'email', 'password', 'org']

    def form_valid(self, form):
        return super().form_valid(form)

# TODO: Should be allow the user to update the password from this view?
class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'Users/user-form.html'
    fields = ['name', 'email', 'org']

    def form_valid(self, form):
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'Users/user-confirm-delete.html'
    success_url = '/'
