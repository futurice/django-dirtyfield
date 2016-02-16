from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory, TransactionTestCase
from django.test.client import Client
from django.utils.timezone import now

from .models import Publication, Article, Publisher, ArticleMedia

from collections import Counter
from pprint import pprint as pp
import os, copy, time, shutil

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

    def test_default_value_used(self):
        publisher = Publisher()
        self.assertNotEquals(publisher.get_changes()['created']['old'], None)
        self.assertNotEquals(publisher.get_changes()['important']['old'], None)
        self.assertNotEquals(publisher.get_changes()['most_important']['old'], None)

    def test_old_value_is_default_value(self):
        publisher = Publisher()
        self.assertEquals(publisher.get_changes()['important']['old'], 1)
        publisher.important = 1
        self.assertEquals(publisher.get_changes()['important']['old'], 1)
        self.assertEquals(publisher.get_changes()['important']['new'], 1)
        publisher.important = 2
        self.assertEquals(publisher.get_changes()['important']['old'], 1)
        self.assertEquals(publisher.get_changes()['important']['new'], 2)
        publisher.important = 3
        self.assertEquals(publisher.get_changes()['important']['old'], 1)
        self.assertEquals(publisher.get_changes()['important']['new'], 3)

    def test_old_value_is_first_value_even_on_assignment(self):
        publisher = Publisher(important=2)
        self.assertEquals(publisher.get_changes()['important']['old'], 2)
        self.assertEquals(publisher.get_changes()['important']['new'], 2)
        publisher.important = 3
        self.assertEquals(publisher.get_changes()['important']['old'], 2)
        self.assertEquals(publisher.get_changes()['important']['new'], 3)
        publisher.important = 4
        self.assertEquals(publisher.get_changes()['important']['old'], 2)
        self.assertEquals(publisher.get_changes()['important']['new'], 4)

    def test_old_value_is_first_value(self):
        publisher = Publisher()
        publisher.name = 'Michael'
        self.assertEquals(publisher.get_changes()['name']['old'], u'')
        self.assertEquals(publisher.get_changes()['name']['new'], 'Michael')
        publisher.name = 'Jason'
        self.assertEquals(publisher.get_changes()['name']['old'], u'')
        self.assertEquals(publisher.get_changes()['name']['new'], 'Jason')

    def test_extra_source_displays_own_fields_only_and_resets_on_save(self):
        article = Article()
        article.headline = 'How to learn anything in five minutes'
        article.fielda = 'A'
        self.assertEquals(article.get_changes(), {'headline': {'new': 'How to learn anything in five minutes', 'old': u''}})
        self.assertEquals(article.get_changes('extra'), {'fielda': {'new': 'A', 'old': None}})
        article.save()
        self.assertEquals(article.get_changes(), {})
        self.assertEquals(article.get_changes('extra'), {})

    def test_filefield(self):
        def up(path, data):
            f = open(path, 'w')
            f.write(data)
            f.close()
            df = File(open(path, 'r'))
            os.remove(path)
            return df
        upload = up('upload.txt', 'upload')
        am = ArticleMedia()
        am.upload = upload
        self.assertEquals(
            am.get_changes(),
            {'upload': {'new': upload, 'old': ArticleMedia().upload}})
        self.assertTrue('upload.txt' in am.get_changes()['upload']['new'].path)
        am.save()
        self.assertEquals(am.get_changes(), {})

        upload2 = up('upload_two.txt', 'upload')

        am_state = am.upload
        am = ArticleMedia.objects.get(pk=am.pk)
        am.upload = upload2
        self.assertEquals(
            am.get_changes(),
            {'upload': {'new': upload2, 'old': am_state}})
        self.assertTrue('upload_two.txt' in am.get_changes()['upload']['new'].path)
        self.assertFalse('upload_two.txt' in am.get_changes()['upload']['old'].path)

        shutil.rmtree('uploads/')
