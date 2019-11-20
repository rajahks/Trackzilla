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
from django.contrib.auth.decorators import login_required
from apps.Resource.models import Resource

import logging
logger = logging.getLogger(__name__)

@login_required
def home(request):
    """Users  landing page
    
    Arguments:
        request {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """

    # Right pane - block 1 - Resources needing action. We need to fetch the list of devices
    # which the users needs to ack or deny
    # Send this as a list as part of dict
    needActionList = []
    resNeedActionQset = Resource.objects.filter(current_user__id=request.user.id).filter(status='R_ASS') #TODO: Use macro instead of R_ASS
    for res in resNeedActionQset:
        needActEntryDict = {}
        needActEntryDict['name'] = res.name
        needActEntryDict['ack_url'] = request.build_absolute_uri(res.get_acknowledge_url())
        needActEntryDict['deny_url'] = request.build_absolute_uri(res.get_deny_url())
        needActEntryDict['detail_url'] = request.build_absolute_uri(res.get_absolute_url())
        needActionList.append(needActEntryDict)

    #TODO: Show resources in conflict in a separate block

    # Right Pane - block 2 - Resources in your name and acknowledged
    inUseList = []
    resInUseQset = Resource.objects.filter(current_user__id=request.user.id).filter(status='R_ACK')
    for res in resInUseQset:
        inUseEntryDict = {}
        inUseEntryDict['name'] = res.name
        inUseEntryDict['update_url'] = request.build_absolute_uri(res.get_update_url())
        inUseEntryDict['detail_url'] = request.build_absolute_uri(res.get_absolute_url())
        inUseList.append(inUseEntryDict)

    # Resources in you teams
    # Since user could be part of more than 1 team, we need to fetch all the teams he is part of
    teamResourceDict = {} # List of resource objects in the team
    try:
        logged_in_user = AssetUser.objects.get(id=request.user.id)
        team_list = logged_in_user.team_member_of.all()
        for team in team_list:
            teamResourceList = []
            # Find out all the members of the team
            members = team.team_members.all()
            # Now for each member we need to find all the resources he owns and 
            # then add it to the list
            for member in members:
                teamResourceList += member.res_being_used.all()

            # Add the team resource list against the team name in teamResourceDict
            teamResourceDict[team.team_name] = teamResourceList
    except:
        # The call AssetUser.objects.get can fail for root user created from command line
        # as it will not be part of the AssetUser table. Log the error as of now
        # TODO: Catch the right error and come up with a better way
        logger.error("AssetUser.objects.get call failed for user %s id%d"%(request.user.get_username(),request.user.id))

    # Resources you are managing
    resBeingManagedList = Resource.objects.filter(device_admin__id=request.user.id)

    context = { "needActionList" : needActionList,
                "inUseList" : inUseList,
                "teamResourceDict" : teamResourceDict,
                "managedDeviceList" : resBeingManagedList,
    }

    return render(request, 'Users/home.html', context=context)


#TODO: Hackfest Addition. Not sure why this was added. This maynot be required.
def people_list(request):
    context = {
        'people': AssetUser.objects.all()   #TODO: Needs to be ORG specific.
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
