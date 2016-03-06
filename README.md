
django-dirtyfield
=================
* [Django-dirtyfield](https://github.com/futurice/django-dirtyfield) [![Build Status](https://travis-ci.org/futurice/django-dirtyfield.svg?branch=master)](https://travis-ci.org/futurice/django-dirtyfield)

**django-dirtyfield** tracks changes to model instances.


Usage
-----

Inherit from `djangodirtyfield.mixin.DirtyFieldMixin`

```python
class MyModel(models.Model, DirtyFieldMixin):
    pass
```

Call `get_changes()` to list modifications.

Multiple sources
----------------

It is possible to track and namespace specified fields, eg. if you're using the model to sync with LDAP.

```python
class ModelLdapDirtyField(DirtyFieldMixin):
    sources = {'default': {'state': '_original_state', 'lookup': '_as_dict', 'fields': 'get_fields'},
            'ldap': {'state': '_ldap_original_state', 'lookup': '_ldap_as_dict', 'fields': 'get_ldap_fields'}}
    def _ldap_as_dict(self, *args, **kwargs):
        fields = {}
        for k,v in getattr(self, 'ldap_only_fields', {}).iteritems():
            fields.update({k: getattr(self, k, '')})
        return fields

    def get_ldap_fields(self):
        return {'get_ldap_cn': 'cn',
                'username': ['uid'],
                'first_name':'givenName'}

class MyModel(ModelLdapDirtyFieldMixin):
    pass
```

Call `get_changes()` to list modifications for states `default` and `ldap`.
