from django.test import SimpleTestCase
from django.urls import resolve, reverse

from . import views


class InputParsingTests(SimpleTestCase):
    def test_parse_positive_int_accepts_positive_numbers(self):
        self.assertEqual(views.parse_positive_int("42"), 42)

    def test_parse_positive_int_rejects_invalid_values(self):
        for value in (None, "", "abc", "0", "-2"):
            with self.subTest(value=value):
                self.assertIsNone(views.parse_positive_int(value))


class UrlTests(SimpleTestCase):
    def test_homepage_route(self):
        match = resolve(reverse("homepage"))
        self.assertIs(match.func, views.homepage)

    def test_analytics_route(self):
        match = resolve(reverse("analytics"))
        self.assertIs(match.func, views.analytics_page)

