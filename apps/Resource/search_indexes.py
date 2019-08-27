from haystack import indexes
from apps.Resource.models import Resource

class ResourceIndex(indexes.SearchIndex, indexes.Indexable):
    # The main "document" field which would be tokenized by the search engines and indexed.
    # The content to use for tokenizing and parsing has been specified in the template
    # "resource_text.txt". The fields specified in the template are what would be searchable.
    text = indexes.CharField(document=True, use_template=True,
                             template_name="search/resource_text.txt")

    # Specify other attributes as fields so that we can use them as filters.

    # TODO: Add the organization as an attribute that is stored along with each record.
    # We would later want to restrict the search to only search the entries belonging to
    # the org of the current logged in user. We do not want the user to see Resources
    # belonging to other orgs.
    # Eg: serialNum = indexes.CharField(model_attr="serial_num")

    def get_model(self):
        return Resource

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

