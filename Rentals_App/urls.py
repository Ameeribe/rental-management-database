from django.urls import path

from . import views


urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("queries/", views.queries_page, name="queries"),
    path("rentals/add/", views.add_rental_page, name="add_rental"),
    path("analytics/", views.analytics_page, name="analytics"),
]
