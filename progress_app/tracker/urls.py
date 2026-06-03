from django.urls import path
from . import views, api_views

app_name = "tracker"

urlpatterns = [
    path("", views.home, name="home"),
    path("add/", views.add_goal, name="add_goal"),
    path("edit/<int:goal_id>/", views.edit_goal, name="edit_goal"),
    path("toggle/<int:goal_id>/", views.toggle_done, name="toggle_done"),
    path("delete/<int:goal_id>/", views.delete_goal, name="delete_goal"),
    path("history/", views.history, name="history"),
    path("timeline/<str:tag>/", views.timeline, name="timeline"),
    path("react/<int:goal_id>/<str:reaction_type>/", views.react_goal, name="react_goal"),

    # API endpoints
    path("api/goals/", api_views.goals, name="api_goals"),
    path("api/goals/<int:goal_id>/", api_views.goal_detail, name="api_goal_detail"),
    path("api/goals/<int:goal_id>/toggle/", api_views.toggle_goal, name="api_toggle_goal"),
    path("api/timeline/<str:tag>/", api_views.timeline_api, name="api_timeline"),
    path("api/react/<int:goal_id>/<str:reaction_type>/", api_views.react_goal_api, name="api_react_goal"),
    path("api/history/", api_views.history_api, name="api_history"),
    path("api/tags/", api_views.tag_choices_api, name="api_tags"),
]
