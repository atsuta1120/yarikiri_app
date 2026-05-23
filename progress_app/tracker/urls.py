from django.urls import path
from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.home, name="home"),
    path("add/", views.add_goal, name="add_goal"),
    path("edit/<int:goal_id>/", views.edit_goal, name="edit_goal"),
    path("toggle/<int:goal_id>/", views.toggle_done, name="toggle_done"),
    path("delete/<int:goal_id>/", views.delete_goal, name="delete_goal"),
    path("history/", views.history, name="history"),
]
