from django.urls import path

from .views import AdminListUsersView

app_name = "management"
urlpatterns = [
    path("users-list/", view=AdminListUsersView.as_view(), name="users-list")
]
