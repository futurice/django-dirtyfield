# Adapted from http://stackoverflow.com/questions/110803/dirty-fields-in-django
from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
from pprint import pprint as pp

import random, string, hashlib, time
import six

def id_generator():
    return hashlib.md5(str(time.time()).encode('utf-8')).hexdigest() + str(random.randint(1, 100))

class DirtyFieldMixin(object):
    sources = {'default': {'state': '_original_state', 'lookup': '_as_dict', 'fields': 'get_fields'}}
    def __init__(self, *args, **kwargs):
        super(DirtyFieldMixin, self).__init__(*args, **kwargs)
        post_save.connect(
            self._reset_state, sender=self.__class__,
            dispatch_uid='%s._reset_state_%s'%(self.__class__.__name__, id_generator()))
        self._reset_state(initialize=True)

    def get_fields(self):
        return self._meta.local_fields

    def get_source(self, name, value):
        return getattr(self, self.sources[name][value])

    def _as_dict(self, *args, **kwargs):
        fields = dict([
            (f.attname, getattr(self, f.attname))
            for f in self.get_fields()
        ])
        return fields

    def _reset_state(self, *args, **kwargs):
        for source, v in six.iteritems(self.sources):
            setattr(self, v['state'], getattr(self, v['lookup'])(**kwargs))

    def get_dirty_fields(self, source='default'):
        new_state = self.get_source(source, 'lookup')()
        changed_fields = {}
        if self._state.adding:
            changed_fields = self.get_field_values(source=source, initial_state=True)
        for key,value in six.iteritems(self.get_source(source, 'state')):
            if value != new_state[key]:
                changed_fields.update({key:value})
        return changed_fields

    def as_value(self, value):
        return value() if (value and callable(value)) else value

    def field_has_default_value(self, field_name, source='default'):
        for field in self.get_source(source, 'fields'):
            if field_name == field.name:
                if field.default:
                    return field
        return False

    def get_field_values(self, source='default', initial_state=False):
        changed_fields = {}
        for k in self.get_source(source, 'fields')():
            name = k.name if (not isinstance(k, six.string_types)) else k
            default = k.default if (not isinstance(k, six.string_types)) else None
            field_value = getattr(self, name, None)
            if field_value:
                if initial_state:
                    changed_fields[name] = self.as_value(self.get_source(source, 'state').get(name))
                else:
                    field_value = self.as_value(field_value)
                    default_value = self.as_value(default)
                    if field_value != default_value:
                        changed_fields[name] = field_value
        return changed_fields

    def is_dirty(self, source='default'):
        if not self.pk:
            return True
        return {} != self.get_dirty_fields(source=source)

    def get_changes(self, source='default', dirty_fields=None):
        changes = {}
        if dirty_fields is None:
            dirty_fields = self.get_dirty_fields(source=source)
        for field, old in six.iteritems(dirty_fields):
            field_value = getattr(self, field)
            changes[field] = {'old': old, 'new': field_value}
        return changes

    def get_m2m_relations(self):
        r = []
        for field, model in self._meta.get_m2m_with_model():
            if isinstance(field, models.ManyToManyField):
                r.append(field)
        return r

class TypedDirtyFieldMixin(DirtyFieldMixin):
    def get_content_type(self):
        return ContentType.objects.get_for_model(self)
