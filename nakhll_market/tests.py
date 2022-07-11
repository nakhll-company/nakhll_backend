from unicodedata import category
from nakhll import load_django_settings_for_unittest
from django.test import TestCase
from rest_framework.test import APIClient
# Create your tests here.
from django.contrib.auth.models import User
from nakhll_market.models import Product, Shop, Category


class ShopDetailPageTestCase(TestCase):
    def setUp(self) -> None:
        self.url = '/api/v1/shop/{}/'
        self.published_slug = 'a'
        self.unpublished_slug = 'b'
        user = User.objects.create_user(username='a')
        shop = Shop.objects.create(
            Title=self.published_slug,
            Slug=self.published_slug,
            FK_ShopManager=user,
            Publish=True)
        shop = Shop.objects.create(
            Title=self.unpublished_slug,
            Slug=self.unpublished_slug,
            FK_ShopManager=user,
            Publish=False)
        self.client = APIClient()

    def test_published_shop(self):
        response = self.client.get(self.url.format(self.published_slug))
        self.assertEqual(response.status_code, 200)

    def test_unpublished_shop(self):
        response = self.client.get(self.url.format(self.unpublished_slug))
        self.assertEqual(response.status_code, 400)

    def test_not_found_shop(self):
        response = self.client.get(self.url.format('c'))
        self.assertEqual(response.status_code, 404)


class ProductDetailPageTestCase(TestCase):
    def setUp(self) -> None:
        self.url = '/api/v1/product-page/details/{}/'
        user = User.objects.create_user(username='a')
        category = Category.objects.create(name='a', slug='a')
        Shop.objects.create(
            Title='a',
            Slug='a',
            FK_ShopManager=user,
            Publish=True)
        Shop.objects.create(
            Title='b',
            Slug='b',
            FK_ShopManager=user,
            Publish=False)
        Product.objects.create(
            Title='a',
            Slug='a',
            FK_Shop=Shop.objects.get(Title='a'),
            Publish=True,
            Price=1000,
            category=category,
        )
        Product.objects.create(
            Title='b',
            Slug='b',
            FK_Shop=Shop.objects.get(Title='a'),
            Publish=False,
            Price=1000,
            category=category,
        )
        Product.objects.create(
            Title='c',
            Slug='c',
            FK_Shop=Shop.objects.get(Title='b'),
            Publish=True,
            Price=1000,
            category=category,
        )
        Product.objects.create(
            Title='d',
            Slug='d',
            FK_Shop=Shop.objects.get(Title='b'),
            Publish=False,
            Price=1000,
            category=category,
        )
        self.client = APIClient()

    def test_published_product(self):
        response = self.client.get(self.url.format('a'))
        self.assertEqual(response.status_code, 200)

    def test_unpublished_product_raise_error(self):
        response = self.client.get(self.url.format('b'))
        self.assertEqual(response.status_code, 400)
        response = self.client.get(self.url.format('d'))
        self.assertEqual(response.status_code, 400)

    def test_unpublish_shop_raise_error(self):
        response = self.client.get(self.url.format('c'))
        self.assertEqual(response.status_code, 400)
