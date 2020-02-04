from django.shortcuts import render
from django.http import HttpResponse

# For the resource update view
from django.contrib.auth import get_user_model  # Current user model
from django.shortcuts import get_object_or_404, redirect

# Haystack imports for Search
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet
from haystack.forms import SearchForm
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
from apps.Users.mixin import UserHasAccessToResourceMixin

# Imports required for Mail
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.sites.models import Site

# imports required for acknowledge and deny views
from django.http import HttpResponseForbidden, Http404
from django.contrib.auth.decorators import login_required

from .forms import ResourceCreateForm, ResourceUpdateForm
from django.views import View
from apps.Users.middleware import get_current_org

# Logging
import logging

logger = logging.getLogger(__name__)

# Get the current custom User Model.
User = get_user_model()


def resources_list(request):
    context = {
        'resources': Resource.objects.all()  # TODO: Needs to be ORG specific.
    }
    return render(request, 'Resource/resources_list.html', context)


class ResourceSearchView(LoginRequiredMixin, SearchView):
    """Custom SearchView to tweak the search behavior performed on the resources.

    Arguments:
        SearchView -- Generic view provided by Haystack.
        Reference -- https://django-haystack.readthedocs.io/en/latest/views_and_forms.html#upgrading
    """

    template_name = 'search/search.html'
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
        if spell_suggestion is not None and query.casefold() != spell_suggestion.casefold():
            context['spell_suggestion'] = spell_suggestion  # Can this ever be a list?

        return context

    def get_queryset(self):
        cur_user_org = get_current_org()

        # In case we want all results. But we want Org specific results, hence
        # commented the below line and added the filter.
        # queryset = SearchQuerySet().all()

        # SearchQuerySet().all() returns all records. However, we want to restrict the
        # results to the currently logged in users org. We save the Resource's org as an
        # integer attribute in each record. Filter the results using that.
        # This is very important else people from different orgs will be shown resources
        # not in their org.
        if cur_user_org is None:
            queryset = SearchQuerySet().none()
        else:
            queryset = SearchQuerySet().filter(org_id=cur_user_org.id)
        return queryset


@login_required
def autocomplete(request):
    """View called when the url 'search/autocomplete/' is hit. It is called using
    a AJAX call when the user enters text

    Arguments:
        request {HttpRequest} -- Standard Django Request object

    Returns:
        [json] -- returns a json response containing a list of suggestions which
                  would match the user's input. List set against a key 'suggestions'
    """
    cur_user_org = get_current_org()

    if cur_user_org is None:
        sqs_org = SearchQuerySet().none()
    else:
        sqs_org = SearchQuerySet().filter(org_id=cur_user_org.id)

    sqs = sqs_org.autocomplete(device_name_auto=request.GET.get('query', ''))
    # TODO: [:5] at the end of the above sqs statement to display only top 5
    suggestions = [result.object.name for result in sqs]
    # Make sure you return a JSON object, not a bare list.
    # Otherwise, you could be vulnerable to an XSS attack.
    the_data = json.dumps({
        'suggestions': suggestions
    })
    return HttpResponse(the_data, content_type='application/json')


class ResourceDetailViewOld(LoginRequiredMixin, UserHasAccessToResourceMixin, UpdateView):
    model = Resource
    template_name = 'Resource/resource-form.html'   # <app>/<model>_<viewtype>.html
    form_class = ResourceDetailForm


class ResourceDetailView(LoginRequiredMixin, UserHasAccessToResourceMixin, View): #TODO: Add has permission mixin
    """View which handles the detail view of a Resource.
    It queries the object and creates a custom form object ResourceDetailForm which
    makes all items readonly.
    """
    def get(self, request, *args, pk, **kwargs):
        resource = get_object_or_404(Resource, pk=pk)
        resource_form = ResourceDetailForm(instance=resource, org=resource.org)
        context = {'form': resource_form, 'org': resource.org, 'resource': resource}
        return render(request, 'Resource/resource-detail.html', context=context)


class ResourceHistoryView(LoginRequiredMixin, UserHasAccessToResourceMixin, View):  #TODO: Add has permission mixin
    """ View to handle showing the history of changes to a resource"""

    def get(self, request, *args, pk, **kwargs):
        resource = get_object_or_404(Resource, pk=pk)
        # Process the history records before showing them. We perform the following
        # 1) Capitalize and replaces '_' with space like labels so that they look good.
        # 2) Remove the 'previous_user' entry as it redundant. 'current_user' is enough
        #    to see how the resource moved. 'previous_user' was only required to handle
        #    sending 3 way mails when device in disputed state.
        resource_history = resource.history
        for resEntry in resource_history:
            listOfChangeDict = resEntry['what']
            for changeEntryDict in list(listOfChangeDict):
                if changeEntryDict['field'] == 'previous_user':
                    listOfChangeDict.remove(changeEntryDict)
                    continue
                # for other fields Capitalize the first letter and replace underscore
                # with spaces.
                formatted_field_name = changeEntryDict['field']
                formatted_field_name = formatted_field_name.capitalize()
                formatted_field_name = formatted_field_name.replace('_', ' ')
                changeEntryDict['field'] = formatted_field_name

        context = {'org': resource.org, 'resource': resource,
            'history_list': resource_history}
        return render(request, 'Resource/resource-history.html', context=context)


class ResourceCreateView(LoginRequiredMixin, View):
    """View to handle Resource Creation.

    Arguments:
        LoginRequiredMixin -- Ensures user has to login before trying to create a resource.
        View -- CBV to handle view.
    """

    def get(self, request, *args, **kwargs):
        """Creates and shows an empty ResourceCreateForm to allow creation of resource.
        """
        current_org = get_current_org()
        resource_form = ResourceCreateForm(in_org=current_org)
        context = {'form': resource_form, 'org': current_org}
        return render(request, 'Resource/resource-new.html', context=context)

    def post(self, request, *args, **kwargs):
        """Handles validation and saving of a resource. Before saving, it changes
        the 'org' param to point to the user's org so that the resource belongs to that
        org. Also sets the resource to assigned state. It also triggers a mail to
        current_user and device_admin that a resource was created and assigned to them.
        """
        current_org = get_current_org()
        resource_form = ResourceCreateForm(request.POST, in_org=current_org)
        if resource_form.is_valid():
            resource_obj = resource_form.save(commit=False)
            resource_obj.org = current_org
            resource_obj.status = Resource.RES_ASSIGNED
            # Finally save the object into the DB
            resource_obj.save()
            # TODO: A mail has to be sent to the device admin that a new resource was added
            # and also that the resource has been assigned to him.
            context = {'device': resource_obj}
            return render(request, 'Resource/resource-creation-success.html', context=context)
        else:
            # Form is invalid. Display the form back to user with errors.
            context = {'form': resource_form, 'org': current_org}
            return render(request, 'Resource/resource-new.html', context=context)


# TODO: "Only an Admin can have update rights of fields other than current user".
class ResourceUpdateView(LoginRequiredMixin, UserHasAccessToResourceMixin, View):

    def get(self, request, *args, pk, **kwargs):
        resource = get_object_or_404(Resource, pk=pk)
        resource_form = ResourceUpdateForm(instance=resource, in_org=resource.org)
        context = {'form': resource_form, 'org': resource.org}
        return render(request, 'Resource/resource-update.html', context=context)

    def post(self, request, *args, pk, **kwargs):
        """Handles validation and saving of a resource. Before saving, it changes
        the 'org' param to point to the user's org so that the resource belongs to that
        org. Also sets the resource to assigned state. It also triggers a mail to
        current_user and device_admin that a resource was created and assigned to them.
        """
        current_org = get_current_org()
        res_in_db = get_object_or_404(Resource, pk=pk)
        resource_form = ResourceUpdateForm(request.POST, in_org=current_org,
                                           instance=res_in_db)
        if resource_form.is_valid():
            # Before we save the data, we need to perform few operations
            # 1) If the current_user has changed, we need to save the previous current_user in
            #    previous_user field and also send out a mail to the new user.
            # 2) If the user has changed then we need to reset the status to Assigned

            resource_obj = resource_form.save(commit=False) # extract the model object.

            hasOwnershipChanged = False # Flag to keep track if device was reassigned
            if resource_form.has_changed() and 'current_user' in resource_form.changed_data:
                # The current user field has changed, there was a reassignment.
                # Fetch the previous user id and name.
                prev_user_id = resource_form.initial['current_user']
                previous_user = None
                try:
                    userModel = get_user_model()
                    previous_user = userModel.objects.get(pk=prev_user_id)
                except userModel.Doesnotexit:
                    logger.warning("Get of prev_user_id: %d failed"%(prev_user_id,))  #TODO: is this ever possible for previous. User object getting deleted when updated?

                resource_obj.previous_user = previous_user
                resource_obj.status = Resource.RES_ASSIGNED
                hasOwnershipChanged = True

            # Finally save the object into the DB
            resource_obj.save()

            # If there was a reassignment, send a mail to the new user.
            if hasOwnershipChanged:
                # Form the ack and deny links by fetching the relative portion from the resource
                ack_url = self.request.build_absolute_uri(resource_obj.get_acknowledge_url())
                deny_url = self.request.build_absolute_uri(resource_obj.get_deny_url())

                # TODO: The from_email should ideally be read from common settings.
                ret = sendAssignmentMail(from_email=settings.EMAIL_FROM_ADDRESS,
                        to_email=resource_obj.current_user.email,
                        cur_user=resource_obj.current_user.get_username(),
                        prev_user=resource_obj.previous_user.get_username(),
                        device_name=resource_obj.name, ack_link=ack_url,
                        decline_link=deny_url)

                if ret == 0:
                    # Sending the email failed. Log an error
                    logger.error("Sending an assignment email failed. Device:%s cur_user:%s cur_user_email:%s prev_user:%s"
                        % (resource_obj.name, resource_obj.current_user.get_name(),
                          resource_obj.current_user.get_email(),
                          resource_obj.previous_user.get_name()))

            # On successfull update, redirect to the detail page.
            return redirect('Resource:resource-detail',pk=resource_obj.pk)
        else:
            # Form is invalid. Display the form back to user with errors.
            context = {'form': resource_form, 'org': current_org}
            return render(request, 'Resource/resource-update.html', context=context)


class ResourceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Resource
    template_name = 'Resource/resource-confirm-delete.html'
    success_url = '/'
    context_object_name = 'resource'

    # Implement the function called by UserPassesTestMixin
    # Only the device admin should have delete rights.
    def test_func(self):
        resource = self.get_object()
        if self.request.user.id == resource.device_admin.id:
            return True

        logger.warning("User %s DENIED access to DeleteView of %s as not an Admin of the device." %
            (self.request.user.get_email(), resource.get_name()))
        return False


def sendAssignmentMail(from_email, to_email, cur_user, prev_user,
                       device_name, ack_link, decline_link):
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

    subject = device_name + " asssigned"

    context = {'cur_user': cur_user, 'device_name': device_name,
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



#TODO: include additional check that the resource belongs to his org.
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

#TODO: include additional check that the resource belongs to his org.
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

    # Check the status and dispute it it not disputed already.
    if resBeingDenied.status != Resource.RES_DISPUTE:
        resBeingDenied.status = Resource.RES_DISPUTE
        resBeingDenied.save()
        logger.info('Device %s disputed by user %s' % (resBeingDenied.name,
            loggedInUser.get_username()))
        # Trigger an email to inform users about the dispute.
        # Email to be sent to Current_user, prev_user and device_admin.
        url = request.build_absolute_uri(resBeingDenied.get_absolute_url())
        res = resBeingDenied

        to_email_list = [res.current_user.email, res.device_admin.email]
        if res.previous_user is not None:
            to_email_list.append(res.previous_user.email)
            prev_user_uname = res.previous_user.get_username()
        else:
            # When the resource is created and assigned to a user, previous_user is None
            # as the resource is not yet reassigned.
            # Show as "None" in such a case.
            prev_user_uname = 'None'

        ret = sendDisputeMail(from_email=settings.EMAIL_FROM_ADDRESS,
                to_email_list=to_email_list,
                cur_user=res.current_user.get_username(),
                prev_user=prev_user_uname,
                device_admin=res.device_admin.get_username(),
                device_name=res.name, device_url=url)
        if ret == 0:
            logger.error("Failed to send email for device dispute. Device:%s cur_user:%s prev_user:%s"%
                (res.name, res.current_user.get_username(), prev_user_uname))
    else:
        logger.info('Device %s already in Disputed state. user %s' % (resBeingDenied.name,
            loggedInUser.get_username()))

    # In case we try to Deny a device already in Disputed state, prev_user_uname is
    # unassigned. Assign the variable here
    if resBeingDenied.previous_user:
        prev_user_uname = resBeingDenied.previous_user.get_username()
    else:
        prev_user_uname = "None"

    context = {'cur_user': resBeingDenied.current_user.get_username(),
               'prev_user': prev_user_uname,
               'device_name': resBeingDenied.name,
               'device_admin': resBeingDenied.device_admin.get_username(), }

              # TODO: previous_user maybe None if this device was never assigned and the
              # deny url is hit for the device. Handle it.
              # UPDATE: This has been mostly handled by checking if prev_user is None and
              # only then accessing the username and email. Showing username as "None" if
              # previous_user in None.

    # Return a warning message that the resource is now in Disputed state.
    return render(request, template_name='Resource/deny.html', context=context)


def send_summary_email(user):
    """Function when called sends a summary report to the user by email.
    The summary email will contain the following data:
        1) Resources in dispute with Resource Ack link.
        2) Resources being managed which are in Dsipute.
        3) Resources needing action ( To be ack'd or denied ) with Ack & Deny links.
        2) Resources in use - With reassign button which would lead to the Resource update page.
        4) Home page Button - Button with link to home page for performing other actions.

    """
    res_in_dispute = user.res_being_used.filter(status=Resource.RES_DISPUTE)
    res_needing_action = user.res_being_used.filter(status=Resource.RES_ASSIGNED)
    res_in_use = user.res_being_used.filter(status=Resource.RES_ACKNOWLEDGED)
    res_managed_in_dispute = user.res_being_managed.filter(
        status=Resource.RES_DISPUTE)
    current_site = Site.objects.get_current()
    domain_url = "http://%s" % (current_site.domain,)
    subject = "Device Summary"
    from_email = settings.EMAIL_FROM_ADDRESS
    to_email = user.get_email()

    # We do not need to send an email if the user has no resources in his name or has to
    # take any action.
    if (len(res_in_dispute) == 0 and len(res_needing_action) == 0 and
            len(res_in_use) == 0 and len(res_managed_in_dispute) == 0):
        return -1

    context = {'res_in_dispute': res_in_dispute,
                'res_needing_action': res_needing_action,
                'res_in_use': res_in_use,
                'res_managed_in_dispute': res_managed_in_dispute,
                'current_site': current_site,
                'domain_url': domain_url,
                'user': user}

    html_message = render_to_string('mail/summary.html', context)
    plain_message = strip_tags(html_message)

    ret = mail.send_mail(subject, plain_message, from_email, [to_email],
                         html_message=html_message)

    if ret == 0:
        logger.error("Sending email failed for user %s" % (user.get_email()))

    # If the above mail is causing issues, use the below to send html only email
    # hmsg = EmailMessage(subject, html_message, from_email, [to])
    # hmsg.content_subtype = "html"  # Main content is now text/html
    # ret = hmsg.send()

    return ret


def send_summary_email_for_all():
    """Helper API to trigger sending 'send_summary_email' for each user.
    We should trigger this from a cron job.
    """
    # Variables to keep track of how many emails were sent, skipped and failed.
    emailSentCount: int = 0
    emailSkippedCount: int = 0
    emailFailedCount: int = 0

    for user in User.objects.all():  # User = get_user_model()
        result = send_summary_email(user)
        # Update the counter variables
        if result == 1:
            emailSentCount += 1
        elif result == 0:
            emailFailedCount += 1
        else:  # result == -1
            emailSkippedCount += 1

    logger.info("Summary Email sent for all users. Total_users:(%d) Emails_sent:(%d)"
        " Emails_skipped:(%d) Emails_failed:(%d)" % (User.objects.count(), emailSentCount,
        emailSkippedCount, emailFailedCount))
