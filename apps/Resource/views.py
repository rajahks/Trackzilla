from django.shortcuts import render
from django.http import HttpResponse

# For the resource update view
from apps.Users.models import AssetUser
from django.shortcuts import redirect

# Haystack imports for Search
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet
from haystack.forms import SearchForm, ModelSearchForm
# Imports for autocomplete
import simplejson as json

# Imports for CRUD views
from .forms import ResourceDetailForm
from .models import Resource
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

#Imports required for Mail
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMessage

# imports required for acknowledge and deny views
from .models import Resource
from django.http import HttpResponseForbidden, Http404
from django.contrib.auth.decorators import login_required

# Logging
import logging

logger = logging.getLogger(__name__)


def resources_list(request):
    context = {
        'resources': Resource.objects.all()
    }
    return render(request, 'Resource/resources_list.html', context)


class ResourceSearchView(SearchView):
    """Custom SearchView to tweak the search behavior performed on the resources.

    Arguments:
        SearchView -- Generic view provided by Haystack.
        Reference -- https://django-haystack.readthedocs.io/en/latest/views_and_forms.html#upgrading
    """

    template_name = 'search/search.html'
    queryset = SearchQuerySet().all()
    # TODO: Filter SearchQuerySet to contain only resources belonging to the user's org
    # queryset = SearchQuerySet().filter(org='<orgOfUser>') OR override get_queryset()
    form_class = SearchForm  # Use ModelSeachForm if we need to restrict search to only few models

    def get_context_data(self, *args, **kwargs):
        context = super(ResourceSearchView, self).get_context_data(*args, **kwargs)
        # Add any additional context data we need to display in forms

        # Fetch the suggestions and add it to context so that it can be displayed to user
        # The suggestions seem to be correcting spelling mistakes only and only if nearby
        # words are in the search index. Eg: If we search for 'lenova' it suggests 'lenovo'
        # or say 'touchscren' it would suggest 'touchscreen'
        # It does not seem to be correcting words which are not in the db and may not
        # correct always. In such a case it returns the query word itself. So Only add if
        # we received a different suggestion

        spell_suggestion = self.get_form().get_suggestion()
        query = context['query']
        if spell_suggestion != None and query.casefold() != spell_suggestion.casefold():
            context['spell_suggestion'] = spell_suggestion  # Can this ever be a list?

        return context


def autocomplete(request):
    sqs = SearchQuerySet().autocomplete(device_name_auto=request.GET.get('query', ''))
    # TODO: [:5] at the end of the above sqs statement to display only top 5
    suggestions = [result.object.name for result in sqs]
    # Make sure you return a JSON object, not a bare list.
    # Otherwise, you could be vulnerable to an XSS attack.
    the_data = json.dumps({
        'suggestions': suggestions
    })
    return HttpResponse(the_data, content_type='application/json')


class ResourceDetailView(UpdateView):
    model = Resource
    template_name = 'Resource/resource-form.html'   # <app>/<model>_<viewtype>.html
    form_class = ResourceDetailForm


class ResourceCreateView(LoginRequiredMixin, CreateView):
    model = Resource
    # This CBV expects a template named resource_form.html. Overriding.
    template_name = 'Resource/resource-form.html'
    # CreateView class will automatically display for us a form asking for these fields.
    # TODO : Should we ask for device_admin or automatically set it to the logged in user?
    fields = ['name', 'serial_num', 'current_user', 'device_admin', 'status', 'description', 'org_id']

    def form_valid(self, form):
        # TODO : Add this if we're automatically setting device admin.
        # form.instance.device_admin = self.request.user
        return super().form_valid(form)


class ResourceUpdateView(LoginRequiredMixin, UpdateView):
    model = Resource
    template_name = 'Resource/resource-form.html'
    fields = ['name', 'serial_num', 'current_user', 'device_admin', 'status', 'description', 'org_id']
    # TODO: Set the context_object_name to resource so that we can access as resource instead of object.

    def form_valid(self, form):
        # Before we save the data, we need to perform few operations
        # 1) If the current_user has changed, we need to save the previous current_user in
        #    previous_user field and also send out a mail to the new user.
        # 2) If the user has changed then we need to reset the status to Assigned

        if form.has_changed() and 'current_user' in form.changed_data:
            # The current user field has changed.
            #TODO: Can this even be None ? and why is this returning an ID instead of user object
            # Is it because we are not supplying a model form?
            prev_user_id = form.initial['current_user']
            previous_user = None
            try:
                previous_user = AssetUser.objects.get(pk=prev_user_id)
            except AssetUser.Doesnotexit:
                logger.warning("Get of prev_user_id: %d failed"%(prev_user_id,))  #TODO: is this ever possible for previous. User object getting deleted when updated?

            # Get the model from the form and change the fields.
            resource = form.save(commit=False)
            resource.previous_user = previous_user
            resource.status = Resource.RES_ASSIGNED
            # Save the model and then send out an email
            resource.save()
            # Form the ack and deny links by fetching the relative portion from the resource
            ack_url = self.request.build_absolute_uri(resource.get_acknowledge_url())
            deny_url = self.request.build_absolute_uri(resource.get_deny_url())

            ret = sendAssignmentMail( from_email = 'no-reply<no-reply@trackzilla.com',
                        to_email=resource.current_user.email,
                        cur_user=resource.current_user.get_username(),
                        prev_user=resource.previous_user.get_username(),
                        device_name=resource.name, ack_link = ack_url,
                        decline_link = deny_url)

            if ret == 0:
                #Sending the email failed. Log an error
                logger.error("Sending an assignment email failed. Device:%s cur_user:%s cur_user_email:%s prev_user:%s"
                    %(resource.name, resource.current_user.get_username(),
                    resource.current_user.email, resource.previous_user.get_username()))

        # On successfull update, redirect to the detail page.
        return redirect('resource-detail',pk=resource.pk)

    # def test_func(self):
    #     resource = self.get_object()
    #     if self.request.user.id == resource.current_user.id:
    #         return True
    #     return False


class ResourceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Resource
    template_name = 'Resource/resource-confirm-delete.html'
    success_url = '/'

    def test_func(self):
        resource = self.get_object()
        # Only the device admin should have delete rights.
        if self.request.user.id == resource.device_admin.id:
            return True
        return False

def sendAssignmentMail( from_email, to_email, cur_user, prev_user,
                        device_name, ack_link, decline_link ):
    """API to send an email when the device is reassigned.

    Arguments:
        from_email {str} -- Email id to be shown in from section Eg: no-reply<no-reply@trackzilla.com>
        to_email {str} -- Email id of the current user to whom mail should be sent
        cur_user {str} -- Current device user's name or email id
        prev_user {str} -- Previous device user's name or email id
        device_name {str} -- Name of the device
        ack_link {str} -- Link to acknowledge the assignment.
        decline_link {str} -- Link to decline the assignment.

    Returns:
        int -- 1 for success and 0 for failure. (value returned by send_mail api)
    """

    subject =  device_name + " asssigned"

    context = { 'cur_user':cur_user, 'device_name': device_name,
                'prev_user': prev_user, 'ack_link': ack_link,
                'decline_link': decline_link,
              }
    html_message = render_to_string('mail/assigned.html', context )
    plain_message = strip_tags(html_message)

    ret = mail.send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
    # If the above mail is causing issues, use the below to send html only email
    # hmsg = EmailMessage(subject, html_message, from_email, [to])
    # hmsg.content_subtype = "html"  # Main content is now text/html
    # ret = hmsg.send()

    return ret

def sendDisputeMail( from_email, to_email_list, cur_user, prev_user,
                      device_admin, device_name, device_url ):
    """API to send an email when the device is in disputed state.

    Arguments:
        from_email {str} -- Email id to be shown in from section Eg: no-reply<no-reply@trackzilla.com>
        to_email_list {list(str)} -- List of Email id strs to whom mail should be sent
        cur_user {str} -- Current device user's name or email id
        prev_user {str} -- Previous device user's name or email id
        device_admin {str} -- Administrator of the device - Name or email id 
        device_name {str} -- Name of the device
        device_url {str} -- Link which will mostly send the detail or update view of the resource.

    Returns:
        int -- 1 for success and 0 for failure. (value returned by send_mail api)
    """

    subject =  device_name + " in dispute."

    context = { 'cur_user':cur_user, 'device_name': device_name,
                'prev_user': prev_user, 'device_url': device_url,
                'device_admin': device_admin,
              }
    html_message = render_to_string('mail/dispute.html', context )
    plain_message = strip_tags(html_message)

    ret = mail.send_mail(subject, plain_message, from_email, to_email_list, html_message=html_message)
    # If the above mail is causing issues, use the below to send html only email
    # hmsg = EmailMessage(subject, html_message, from_email, [to])
    # hmsg.content_subtype = "html"  # Main content is now text/html
    # ret = hmsg.send()

    return ret

@login_required
def ackResource(request, pk):
    """This view changes the state of the resource to acknowledged. Before doing so it
       checks if the user trying to acknowledge the resource has the resource in his name.

    Arguments:
        request {} -- Standard Django request dictionary which has all the request details
        pk {int} -- Primary key of the resource.

    Returns:
        HttpForbidden : 1) When the user is trying to ack a resource not in his name.
        Http404: 1) Invalid resource id i.e. pk.
        HttpResponse -- Displaying success message if the resource state was changed successfully.
    """

    # Fetch the currently logged in user
    loggedInUser = request.user
    try:
        resBeingAckd = Resource.objects.get(id=pk)   #TODO: use select_related for better performance to fetch user info
    except Resource.DoesNotExist:
        raise Http404("Resource with pk %d doesnot exist." % (pk)) # TODO: Use template for this.

    # The resource exists. Allow only the current owner to Ack it.
    if resBeingAckd.current_user.id != loggedInUser.id:
        return HttpResponseForbidden("<h1> Http 403: Trying to ack a resource which you do not own!! </h1>")
        # TODO: Use a better template for the above message.

    # Check the status and ack it it not ackd already.
    if resBeingAckd.status != Resource.RES_ACKNOWLEDGED:
        resBeingAckd.status = Resource.RES_ACKNOWLEDGED
        resBeingAckd.save()
        logger.info('Device %s ACKd by user %s'% (resBeingAckd.name, loggedInUser.get_username()))
    else:
        logger.info('Device %s already in ACKd state. user %s'% (resBeingAckd.name, loggedInUser.get_username()))

    context = { 'ack_user': loggedInUser.get_username(),
                'device_name': resBeingAckd.name,
              }
    # Return a success message that the resource was Acknowledged
    return render(request, template_name='Resource/ack.html', context=context )

@login_required
def denyResource(request, pk):
    """This view changes the state of the resource to disputed. Before doing so it
       checks if the user trying to dispute the resource has the resource in his name.

    Arguments:
        request {} -- Standard Django request dictionary which has all the request details
        pk {int} -- Primary key of the resource.

    Returns:
        HttpForbidden : 1) When the user is trying to ack a resource not in his name.
        Http404: 1) Invalid resource id i.e. pk.
        HttpResponse -- Displaying success message if the resource state was changed successfully.
    """

    # Fetch the currently logged in user
    loggedInUser = request.user
    try:
        resBeingDenied = Resource.objects.get(id=pk)   #TODO: use select_related for better performance to fetch user info
    except Resource.DoesNotExist:
        raise Http404("Resource with pk %d doesnot exist." % (pk)) # TODO: Use template for this.

    # The resource exists. Allow only the current owner to Ack it.
    if resBeingDenied.current_user.id != loggedInUser.id:
        return HttpResponseForbidden("<h3> Http 403: Trying to ack a resource which you do not own!! </h3>")
        # TODO: Use a better template for the above message.

    # Check the status and ack it it not ackd already.
    if resBeingDenied.status != Resource.RES_DISPUTE:
        resBeingDenied.status = Resource.RES_DISPUTE
        resBeingDenied.save()
        logger.info('Device %s disputed by user %s'% (resBeingDenied.name,
            loggedInUser.get_username()))
        # Trigger an email to inform users about the dispute.
        # Email to be sent to Current_user, prev_user and device_admin.
        url = request.build_absolute_uri(resBeingDenied.get_absolute_url())
        res = resBeingDenied
        ret = sendDisputeMail( from_email = 'no-reply<no-reply@trackzilla.com',
                to_email_list=[ res.previous_user.email, res.current_user.email,
                res.device_admin.email ],
                cur_user=res.current_user.get_username(), prev_user=res.previous_user.get_username(),
                device_admin=res.device_admin.get_username(),
                device_name=res.name, device_url=url)
        if ret == 0:
            logger.error("Failed to send email for device dispute. Device:%s cur_user:%s prev_user:%s"%
                (res.name, res.current_user.get_username(), res.previous_user.get_username() ))
    else:
        logger.info('Device %s already in Disputed state. user %s'% (resBeingDenied.name, loggedInUser.get_username()))

    context = { 'cur_user': resBeingDenied.current_user.get_username(),
                'prev_user': resBeingDenied.previous_user.get_username(),
                'device_name': resBeingDenied.name,
                'device_admin' : resBeingDenied.device_admin.get_username(),
              }
              # TODO: previous_user maybe None if this device was never assigned and the
              # deny url is hit for the device. Handle it.

    # Return a warning message that the resource is now in Disputed state.
    return render(request, template_name='Resource/deny.html', context=context )

