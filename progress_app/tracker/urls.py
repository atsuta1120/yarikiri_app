from django.urls import path
from . import views

app_name = "tracker"

urlpatterns = [
    # 今日の目標と進捗バー
    path("", views.home, name="home"),
     # 目標の新規追加画面
    path("add/", views.add_goal, name="add_goal"),
    
     path("toggle/<int:goal_id>/", views.toggle_done, name="toggle_done"),

     path("save_screenshot/", views.save_screenshot, name="save_screenshot"),

    path("delete/<int:goal_id>/", views.delete_goal, name="delete_goal"),

]
