from django.shortcuts import render
from django.http import HttpResponse

# Haystack imports for Search
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet
from haystack.forms import SearchForm, ModelSearchForm
# Imports for autocomplete
import simplejson as json
# Imports for CRUD views
from django import forms
from .models import Resource
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Logging
import logging

logger = logging.getLogger(__name__)


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


class ResourceDetailForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'serial_num', 'current_user', 'device_admin', 'status', 'description', 'org_id']
    name = forms.CharField(disabled=True)
    serial_num = forms.CharField(disabled=True)
    current_user = forms.IntegerField(disabled=True)
    device_admin = forms.IntegerField(disabled=True)
    status = forms.ChoiceField(disabled=True)
    org_id = forms.IntegerField(disabled=True)
    # TODO : Figure out to make description text area also non editable


class ResourceDetailView(UpdateView):
    model = Resource
    template_name = 'Resource/resource-detail.html'   # <app>/<model>_<viewtype>.html
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


class ResourceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Resource
    template_name = 'Resource/resource-form.html'
    fields = ['name', 'serial_num', 'current_user', 'device_admin', 'status', 'description', 'org_id']

    def form_valid(self, form):
        return super().form_valid(form)

    def test_func(self):
        resource = self.get_object()
        if self.request.user.id == resource.current_user.id:
            return True
        return False


class ResourceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Resource
    template_name = 'Resource/resource-confirm-delete.html'
    success_url = '/'

    def test_func(self):
        resource = self.get_object()
        if self.request.user.id == resource.current_user.id:
            return True
        return False

