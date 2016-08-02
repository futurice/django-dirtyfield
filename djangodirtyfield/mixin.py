# Adapted from http://stackoverflow.com/questions/110803/dirty-fields-in-django
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.contrib.contenttypes.models import ContentType

import random, string, hashlib, time
import six

def id_generator():
    return hashlib.md5(str(time.time()).encode('utf-8')).hexdigest() + str(random.randint(1, 100))

def changed(changes, field):
    if changes.get(field):
        val = lambda s: changes[field][s]
        if val('new') != val('old'):
            return True
    return False

class DirtyField(object):
    def __init__(self, instance):
        self.instance = instance

    def get_m2m_relations(self):
        r = []
        for field, model in self.instance._meta.get_m2m_with_model():
            if isinstance(field, models.ManyToManyField):
                r.append(field)
        return r

    def get_source(self, name, value):
        return getattr(self.instance, self.instance.sources[name][value])

    def get_dirty_fields(self, source='default'):
        new_state = self.get_source(source, 'lookup')()
        changed_fields = {}
        if self.instance._state.adding:
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
            field_value = getattr(self.instance, name, None)
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
        if not self.instance.pk:
            return True
        return {} != self.get_dirty_fields(source=source)

class DirtyFieldMixin(object):
    sources = {'default': {'state': '_original_state', 'lookup': '_as_dict', 'fields': '_get_fields'}}

    def __init__(self, *args, **kwargs):
        self.dirtyfield = DirtyField(instance=self)
        self._dirtyfields_copy = {}
        super(DirtyFieldMixin, self).__init__(*args, **kwargs)
        genuid = lambda s: '%s._%s_state_%s'%(self.__class__.__name__, s, id_generator())
        pre_save.connect(self._presave_state,
                sender=self.__class__,
                dispatch_uid=genuid('state'))
        post_save.connect(self._reset_state,
                sender=self.__class__,
                dispatch_uid=genuid('reset'))
        self._reset_state(initialize=True)

    def _as_dict(self, *args, **kwargs):
        fields = dict([
            (f.attname, getattr(self, f.attname))
            for f in self._get_fields()
        ])
        return fields

    def _get_fields(self):
        return self._meta.local_fields

    def _reset_state(self, *args, **kwargs):
        for source, v in six.iteritems(self.sources):
            setattr(self, v['state'], getattr(self, v['lookup'])(**kwargs))

    def _presave_state(self, sender, instance, **kwargs):
        self.update_dirtyfields_copy()

    def get_changes(self, source='default', dirty_fields=None):
        changes = {}
        if dirty_fields is None:
            dirty_fields = self.dirtyfield.get_dirty_fields(source=source)
        for field, old in six.iteritems(dirty_fields):
            field_value = getattr(self, field)
            changes[field] = {'old': old, 'new': field_value}
        return changes

    def update_dirtyfields_copy(self):
        self._dirtyfields_copy = self.get_changes()

    def get_dirtyfields_copy(self):
        return self._dirtyfields_copy

class TypedDirtyFieldMixin(DirtyFieldMixin):
    def get_content_type(self):
        return ContentType.objects.get_for_model(self)
