from datetime import date

from django.contrib.auth.models import User
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from .models import Goal
from .utils import get_client_id, CLIENT_ID_COOKIE


def home(request):
    """
    今日の目標一覧 + 進捗表示
    ※ここは既存の実装があるはずなので、あなたの現状に合わせて使ってOK
    """
    client_id, is_new = get_client_id(request)

    goals = Goal.objects.filter(client_id=client_id, date=date.today()).order_by("-created_at")

    # 進捗計算（重み合計に対する達成重み割合）
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
        title = request.POST.get("title")
        difficulty = request.POST.get("difficulty")

        weight_map = {"small": 1, "medium": 3, "large": 5}
        weight = weight_map[difficulty]

        Goal.objects.create(
            client_id=client_id,
            title=title,
            difficulty=difficulty,
            weight=weight,
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
    """
    ✅ GET禁止（勝手に再アクセスされる事故防止）
    """
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
    """
    ✅ GET禁止（勝手に再アクセスされる事故防止）
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    client_id, is_new = get_client_id(request)

    goal = get_object_or_404(Goal, id=goal_id, client_id=client_id)
    goal.delete()

    response = redirect("tracker:home")
    if is_new:
        response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response



CLIENT_ID_COOKIE = "yarikiri_client_id"

def get_client_id(request):
    """
    Cookieから client_id を取得。無ければ新規発行して返す。
    ※ Cookieにセットするのはレスポンス側で行う
    """
    cid = request.COOKIES.get(CLIENT_ID_COOKIE)
    if cid:
        return cid, False
    return str(uuid.uuid4()), True
