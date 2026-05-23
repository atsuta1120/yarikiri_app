from django.conf import settings
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from .models import Goal
from .utils import get_client_id, CLIENT_ID_COOKIE

_WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _attach_client_cookie(response, client_id, is_new):
    if is_new:
        response.set_cookie(
            CLIENT_ID_COOKIE,
            client_id,
            max_age=60 * 60 * 24 * 365,
            samesite="Lax",
            httponly=True,
            secure=not settings.DEBUG,
        )
    return response


def home(request):
    client_id, is_new = get_client_id(request)

    today = timezone.localdate()
    goals = Goal.objects.filter(client_id=client_id, date=today).order_by("-created_at")

    total_weight = sum(g.weight for g in goals)
    done_weight = sum(g.weight for g in goals if g.is_done)
    progress = 0 if total_weight == 0 else int(done_weight / total_weight * 100)

    today_str = f"{today.year}年{today.month}月{today.day}日（{_WEEKDAY_JA[today.weekday()]}）"

    response = render(
        request,
        "tracker/home.html",
        {
            "goals": goals,
            "progress_percent": progress,
            "total_weight": total_weight,
            "done_weight": done_weight,
            "today_str": today_str,
        },
    )
    return _attach_client_cookie(response, client_id, is_new)


def add_goal(request):
    client_id, is_new = get_client_id(request)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        difficulty = request.POST.get("difficulty")

        if not title:
            response = render(request, "tracker/add_goal.html", {"error": "タイトルを入力してください"})
            return _attach_client_cookie(response, client_id, is_new)

        weight_map = {"small": 1, "medium": 3, "large": 5}
        if difficulty not in weight_map:
            response = render(request, "tracker/add_goal.html", {"error": "難易度が不正です"})
            return _attach_client_cookie(response, client_id, is_new)

        Goal.objects.create(
            client_id=client_id,
            title=title,
            difficulty=difficulty,
            weight=weight_map[difficulty],
            is_done=False,
            date=timezone.localdate(),
        )

        response = redirect(reverse("tracker:add_goal") + "?added=1")
        return _attach_client_cookie(response, client_id, is_new)

    added = request.GET.get("added") == "1"
    response = render(request, "tracker/add_goal.html", {"added": added})
    return _attach_client_cookie(response, client_id, is_new)


def toggle_done(request, goal_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    client_id, is_new = get_client_id(request)

    goal = get_object_or_404(Goal, id=goal_id, client_id=client_id)
    goal.is_done = not goal.is_done
    goal.save(update_fields=["is_done"])

    response = redirect("tracker:home")
    return _attach_client_cookie(response, client_id, is_new)


def delete_goal(request, goal_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    client_id, is_new = get_client_id(request)

    goal = get_object_or_404(Goal, id=goal_id, client_id=client_id)
    goal.delete()

    response = redirect("tracker:home")
    return _attach_client_cookie(response, client_id, is_new)
