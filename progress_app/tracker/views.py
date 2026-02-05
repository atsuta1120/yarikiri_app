from datetime import date

from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from .models import Goal
from .utils import get_client_id, CLIENT_ID_COOKIE


def home(request):
    client_id, is_new = get_client_id(request)

    goals = Goal.objects.filter(client_id=client_id, date=date.today()).order_by("-created_at")

    total_weight = sum(g.weight for g in goals)
    done_weight = sum(g.weight for g in goals if g.is_done)
    progress = 0 if total_weight == 0 else int(done_weight / total_weight * 100)

    response = render(
        request,
        "tracker/home.html",
        {
            "goals": goals,
            "progress": progress,
            "total_weight": total_weight,
            "done_weight": done_weight,
        },
    )

    if is_new:
        response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60 * 60 * 24 * 365, samesite="Lax")

    return response


def add_goal(request):
    client_id, is_new = get_client_id(request)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        difficulty = request.POST.get("difficulty")

        # バリデーション（最低限）
        if not title:
            response = render(request, "tracker/add_goal.html", {"error": "タイトルを入力してください"})
            if is_new:
                response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60 * 60 * 24 * 365, samesite="Lax")
            return response

        weight_map = {"small": 1, "medium": 3, "large": 5}
        if difficulty not in weight_map:
            response = render(request, "tracker/add_goal.html", {"error": "難易度が不正です"})
            if is_new:
                response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60 * 60 * 24 * 365, samesite="Lax")
            return response

        Goal.objects.create(
            client_id=client_id,
            title=title,
            difficulty=difficulty,
            weight=weight_map[difficulty],
            is_done=False,
            date=date.today(),
        )

        response = redirect("tracker:home")
        if is_new:
            response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60 * 60 * 24 * 365, samesite="Lax")
        return response

    response = render(request, "tracker/add_goal.html")
    if is_new:
        response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response


def toggle_done(request, goal_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    client_id, is_new = get_client_id(request)

    goal = get_object_or_404(Goal, id=goal_id, client_id=client_id)
    goal.is_done = not goal.is_done
    goal.save(update_fields=["is_done"])

    response = redirect("tracker:home")
    if is_new:
        response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response


def delete_goal(request, goal_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    client_id, is_new = get_client_id(request)

    goal = get_object_or_404(Goal, id=goal_id, client_id=client_id)
    goal.delete()

    response = redirect("tracker:home")
    if is_new:
        response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response
