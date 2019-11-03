from django.db import models

import json
from django.forms.models import model_to_dict
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

class HistoryField(models.TextField):
    description = "Essentially a Textfield which stores the JSON representation of the history list."

    def __init__(self, *args, **kwargs):
        super(HistoryField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return json.loads(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return json.loads(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        return json.dumps(value)


class ChangeHistoryMixin(models.Model):
    """
    A model mixin that tracks model fields' values and records the changes made to it in
    JSON format. A new field 'history' is added to the object.
    """

    # Mark as abstract so that a separate table is not created and the history field is
    # included into the existing table.
    class Meta:
        abstract = True

    # History is stored in the field in JSON format. HistoryField is essentially a
    # Textfield with operations to serialize and de-serialize data.
    # TODO: Make the field name configurable like we are allowed in case of template_name in CBV
    # TODO: Should I include Zlib compression like in PickleField() as the history can get quite long ?
    # TODO: Also evaluate if it would be good idea to store History is a separate table. 
    #       One entry for each Resource. Considering this as history can grow quite large.
    #       It would give us the flexibility to trim it down and handle issues.
    #       But having in the same table gives us benefits like ease of access, everything
    #       under one entry.
    # TODO: If we use PostgreSQL, this could also be a JSONField. I didn't want to restrict
    #       the database at this point hence using a custom TextField.
    history = HistoryField(editable=True,default=[])

    # Hook Function, if defined, is called after the model is converted to dict using 
    # model_to_dict function. This is required because at times we would want to handle 
    # certain fields in a certain way Eg: Storing 'username' or email instead of ID value 
    # for ForeignKeys.
    #
    # Example customer Serializer
    # def CustomFieldSerializer(instance, object_dict, *args, **kwargs):
    #   for field in object_dict:
    #     field_val = getattr(instance,field)
    #     if issubclass(field_val.__class__, User):
    #         object_dict[field] = field_val.get_username()

    #     # Add other fields which need customer processing.
    #   return
    history__process_dict_hook = None

    # Set the number of history entries we wish to store.
    # By default there is no limit and entries will be prepended. If a value is set, then
    # while inserting the record into the list we will trim out the extra entires. 
    # The oldest records are removed.
    history__max_entry_count = None

    # In addition to tracking what changed, it is sometimes important to track who changed
    # it as well. This maynot be required to all users or there could be different ways to
    # do this.
    # Making this configurable by allowing the user to specify a function which would return
    # a string which will be stored in the 'who' field.
    # The below field should be set to a function which when called returns a string
    # which will be stored in the 'who' field. Function is not called when it is None.
    history__get_user_hook = None

    def __init__(self, *args, **kwargs):
        super(ChangeHistoryMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        # diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        diffs = [ { "field":k, "prev":v, "cur": d2[k] } for k, v in d1.items() if v != d2[k]]
        #return dict(diffs)
        return diffs

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    @property
    def _dict(self):
        object_dict =  model_to_dict(self, fields=[field.name for field in
                             self._meta.fields])
        # Call the function which allows to perform custom processing on this dict.
        # call it only if the user has declared a customer serializer.
        if self.history__process_dict_hook is not None:
            self.history__process_dict_hook(object_dict=object_dict) # self passed automatically by python.
        return object_dict

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        changesDict = self.diff

        # Let's construct the history record entry and add it to the dict.
        # Each record is further going to be dictionary stored in the DB as a string.

        # We need to keep track of which user updated the data. Check if the user has
        # assigned a callable to fetch it. Else we will initialize it to be empty.
        who = None
        if self.history__get_user_hook is not None:
            if callable(self.history__get_user_hook):
                who = self.history__get_user_hook()
            else:
                logger.error("history_get_user initialized with a non-callable")

        # only add the 'who' field if we have a string value.
        if who is not None and isinstance(who,str):
            entry = {
                "who"  : str(who),
                "when" : timezone.now().isoformat(),
                "what" : changesDict,
            }
        else:
            entry = {
                "when" : timezone.now().isoformat(),
                "what" : changesDict,
            }

        # prepend this entry into the list
        if isinstance(self.history, list):
            self.history.insert(0,entry)
            if isinstance(self.history__max_entry_count, int):
                if self.history__max_entry_count >= 0:
                # Value has been specified. Trim the list. Value of 0 deletes the whole list.
                    del self.history[self.history__max_entry_count: ]
            logger.debug('Added the following record to history:\n %s'%(str(entry),))
        else:
            logger.error("History field not saved initially as list!!")

        # Let's not hold up the save. Save and reset the initial state.
        super(ChangeHistoryMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

