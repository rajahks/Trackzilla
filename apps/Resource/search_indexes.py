from haystack import indexes
from apps.Resource.models import Resource


class ResourceIndex(indexes.SearchIndex, indexes.Indexable):
    # The main "document" field which would be tokenized by the search engines and indexed.
    # The content to use for tokenizing and parsing has been specified in the template
    # "resource_text.txt". The fields specified in the template are what would be searchable.
    text = indexes.CharField(document=True, use_template=True,
                             template_name="search/resource_text.txt")

    # We add this for autocomplete. Currently we are only auto-completing
    # on name. We can extend this in future when we want to include other
    # fields.
    device_name_auto = indexes.EdgeNgramField(model_attr='name')

    # Specify other attributes as fields so that we can use them as filters.

    # Add the organization as an attribute to be stored along with each record.
    # We use this in the SearchView to restrict the search to only search the
    # entries belonging to the org of the current logged in user.
    # We do not want the user to see Resources belonging to other orgs.
    # Since 'id' of the Org is what is unique, we store that as an attribute.
    # This is very important as it allows us to get Org specific results.
    org_id = indexes.IntegerField(model_attr="org__id")

    def get_model(self):
        return Resource

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
