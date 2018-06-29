""" Model factories """

import random
import string
import factory
from factory.fuzzy import FuzzyText
from journals.apps.core.models import User
from wagtail.wagtailcore.models import Page

USER_PASSWORD = 'password'


def random_string_generator(size=5, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class UserFactory(factory.DjangoModelFactory):
    """ Model factory for User model """
    username = factory.Sequence(lambda n: 'user_%d' % n)
    password = factory.PostGenerationMethodCall('set_password', USER_PASSWORD)
    is_active = True
    is_superuser = False
    is_staff = False
    email = factory.Faker('email')
    first_name = FuzzyText()
    last_name = factory.Faker('last_name')
    full_name = factory.LazyAttribute(lambda user: ' '.join((user.first_name, user.last_name)))

    class Meta:
        model = User


class PageFactory(factory.DjangoModelFactory):
    """ Model factory for Page model """

    slug = FuzzyText()
    title = FuzzyText(prefix='page-title')
    path = random_string_generator()
    depth = 1
    numchild = 2

    class Meta:
        model = Page
