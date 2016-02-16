# encoding=utf8
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AbstractUser

from djangodirtyfield.mixin import DirtyFieldMixin

class MultiSourceDirtyFieldMixin(DirtyFieldMixin):
    sources = {'default': {'state': '_original_state', 'lookup': '_as_dict', 'fields': 'get_fields'},
            'extra': {'state': '_extra_state', 'lookup': '_extra_as_dict', 'fields': 'get_extra_fields'}}

    def get_extra_fields(self):
        return ['fielda','fieldb']

    def _extra_as_dict(self, *args, **kwargs):
        fields = {}
        for k in self.sources['extra']['fields']:
            fields.update({k: getattr(self, k, '')})
        return fields

class BaseModel(models.Model, DirtyFieldMixin):
    created = models.DateTimeField(default=now, db_index=True)
    important = models.IntegerField(default=1)

    class Meta:
        abstract = True

class MultiBaseModel(models.Model, MultiSourceDirtyFieldMixin):
    class Meta:
        abstract = True

class Publisher(BaseModel):
    name = models.CharField(max_length=255)
    most_important = models.IntegerField(default=1, null=True, blank=True)

class Publication(BaseModel):
    title = models.CharField(max_length=255)
    publisher = models.ForeignKey(Publisher, null=True, blank=True)

class Article(MultiBaseModel):
    headline = models.CharField(max_length=255)
    publications = models.ManyToManyField(Publication)

class ArticleMedia(models.Model, DirtyFieldMixin):
    upload = models.FileField(upload_to='uploads/')

class User(AbstractUser, DirtyFieldMixin):
    pass
