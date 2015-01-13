# Adapted from http://stackoverflow.com/questions/110803/dirty-fields-in-django
from django.db import models
from django.db.models.signals import post_save
import random, string, hashlib, time

def id_generator():
    return hashlib.md5(str(time.time())).hexdigest() + str(random.randint(1, 100))

class DirtyFieldMixin(object):
    def __init__(self, *args, **kwargs):
        super(DirtyFieldMixin, self).__init__(*args, **kwargs)
        post_save.connect(
            self._reset_state, sender=self.__class__,
            dispatch_uid='%s._reset_state_%s'%(self.__class__.__name__, id_generator()))
        self._reset_state(initialize_dirtyfields=True)

    def _as_dict(self):
        fields = dict([
            (f.attname, getattr(self, f.attname))
            for f in self._meta.local_fields
        ])
        return fields

    def _reset_state(self, *args, **kwargs):
        self._original_state = self._as_dict()

    def get_dirty_fields(self, check_local=False):
        """
        Add any locally set variables on instantiation
        - default value used, if exists, and nothing else set
        """
        new_state = self._as_dict()
        changed_fields = {}
        if self._state.adding:
            changed_fields = self.get_field_values()
        for key,value in self._original_state.iteritems():
            if value != new_state[key]:
                changed_fields.update({key:value})
        return changed_fields

    def get_field_values(self):
        changed_fields = {}
        for k in self._meta.local_fields:
            field_value = getattr(self, k.name)
            if field_value:
                default_value = k.default
                if callable(default_value):
                    default_value = default_value()
                if field_value != default_value:
                    changed_fields[k.name] = field_value
                else:
                    if default_value:
                        changed_fields[k.name] = default_value
        return changed_fields

    def is_dirty(self):
        if not self.pk:
            return True
        return {} != self.get_dirty_fields()

    def get_changes(self, dirty_fields=None):
        """
        Get a dict of changes with existing and new values.
        
        @param instance:     The instance to get changes on.
        @param dirty_fields: If supplied this dict will be used as dirty fields 
                             rather than instance.get_dirty_fields().
        @return dict         A dict of field names which each consist of a dict 
                             containing keys 'existing' and 'new'.
        """
        changes = {}
        if dirty_fields is None:
            dirty_fields = self.get_dirty_fields()
        for field, old in dirty_fields.iteritems():
            field_value = getattr(self, field)
            if callable(field_value):
                field_value = field_value()
            changes[field] = {'old': old, 'new': field_value}
        return changes

    def get_m2m_relations(self):
        r = []
        for field, model in self._meta.get_m2m_with_model():
            if isinstance(field, models.ManyToManyField):
                r.append(field)
        return r
