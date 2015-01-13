from django.conf import settings
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, RequestFactory
from django.utils.timezone import now
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from models import Publication, Article, Publisher

from pprint import pprint as pp
import copy
from collections import Counter

class BaseSuite(TransactionTestCase):
    pass

class DirtyTest(BaseSuite):
    def setUp(self):
        self.user_model = get_user_model()

    def test_dirty(self):
        user = self.user_model.objects.create(username='John')

        p = Publication.objects.create(title='Alice in Wonderland')
        p.title = 'Jane in Wonderland'
        self.assertEquals(p.get_changes(), {'title': {'new': 'Jane in Wonderland', 'old': 'Alice in Wonderland'}})
        p.title = 'Alice in Wonderland'
        self.assertEquals(p.get_changes(), {})
        p.title = 'Jessica in Wonderland'
        p.save()
        self.assertEquals(p.get_changes(), {})
