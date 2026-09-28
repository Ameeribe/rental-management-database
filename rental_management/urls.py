from django.urls import include, path


urlpatterns = [
    path("", include("Rentals_App.urls")),
]

