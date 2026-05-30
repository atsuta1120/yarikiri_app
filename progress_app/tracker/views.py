from collections import defaultdict

from django.conf import settings
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from .models import Goal, Reaction, GoalView
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

    goal_data = []
    for goal in goals:
        reaction_counts = {}
        for rtype, emoji in [('fire', '🔥'), ('clap', '👏'), ('muscle', '💪')]:
            reaction_counts[rtype] = {
                'emoji': emoji,
                'count': goal.reactions.filter(reaction_type=rtype).count(),
            }
        goal_data.append({
            'goal': goal,
            'view_count': goal.views.count(),
            'reaction_counts': reaction_counts,
        })

    response = render(
        request,
        "tracker/home.html",
        {
            "goal_data": goal_data,
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
        tag = (request.POST.get("tag") or "").strip() or "未分類"

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
            tag=tag,
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


def edit_goal(request, goal_id):
    client_id, is_new = get_client_id(request)
    goal = get_object_or_404(Goal, id=goal_id, client_id=client_id)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        difficulty = request.POST.get("difficulty")
        tag = (request.POST.get("tag") or "").strip() or "未分類"

        if not title:
            response = render(request, "tracker/edit_goal.html", {"goal": goal, "error": "タイトルを入力してください"})
            return _attach_client_cookie(response, client_id, is_new)

        weight_map = {"small": 1, "medium": 3, "large": 5}
        if difficulty not in weight_map:
            response = render(request, "tracker/edit_goal.html", {"goal": goal, "error": "難易度が不正です"})
            return _attach_client_cookie(response, client_id, is_new)

        goal.title = title
        goal.difficulty = difficulty
        goal.weight = weight_map[difficulty]
        goal.tag = tag
        goal.save(update_fields=["title", "difficulty", "weight", "tag"])

        response = redirect("tracker:home")
        return _attach_client_cookie(response, client_id, is_new)

    response = render(request, "tracker/edit_goal.html", {"goal": goal})
    return _attach_client_cookie(response, client_id, is_new)


def history(request):
    client_id, is_new = get_client_id(request)

    today = timezone.localdate()
    past_goals = Goal.objects.filter(client_id=client_id, date__lt=today).order_by("-date", "-created_at")

    days = defaultdict(list)
    for goal in past_goals:
        days[goal.date].append(goal)

    history_list = []
    for date in sorted(days.keys(), reverse=True):
        goals = days[date]
        total = sum(g.weight for g in goals)
        done = sum(g.weight for g in goals if g.is_done)
        progress = 0 if total == 0 else int(done / total * 100)
        history_list.append({
            "date": date,
            "date_str": f"{date.year}年{date.month}月{date.day}日（{_WEEKDAY_JA[date.weekday()]}）",
            "goals": goals,
            "progress": progress,
        })

    response = render(request, "tracker/history.html", {"history_list": history_list})
    return _attach_client_cookie(response, client_id, is_new)


REACTION_EMOJI = {
    'fire': '🔥',
    'clap': '👏',
    'muscle': '💪',
}


def timeline(request, tag):
    client_id, is_new = get_client_id(request)
    today = timezone.localdate()

    goals = Goal.objects.filter(tag=tag, date=today).order_by("-created_at")

    # 他人のGoalにのみ閲覧記録を作成
    for goal in goals:
        if goal.client_id != client_id:
            GoalView.objects.get_or_create(goal=goal, client_id=client_id)

    my_reactions = set(
        Reaction.objects.filter(
            goal__in=goals, client_id=client_id
        ).values_list('goal_id', 'reaction_type')
    )

    goal_list = []
    for goal in goals:
        reaction_counts = {}
        for rtype, emoji in REACTION_EMOJI.items():
            count = goal.reactions.filter(reaction_type=rtype).count()
            reaction_counts[rtype] = {
                'emoji': emoji,
                'count': count,
                'reacted': (goal.id, rtype) in my_reactions,
            }
        goal_list.append({
            'goal': goal,
            'is_mine': goal.client_id == client_id,
            'view_count': goal.views.count(),
            'reaction_counts': reaction_counts,
        })

    response = render(request, "tracker/timeline.html", {
        'tag': tag,
        'goal_list': goal_list,
        'today_str': f"{today.year}年{today.month}月{today.day}日（{_WEEKDAY_JA[today.weekday()]}）",
    })
    return _attach_client_cookie(response, client_id, is_new)


def react_goal(request, goal_id, reaction_type):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if reaction_type not in REACTION_EMOJI:
        return JsonResponse({'error': 'invalid reaction'}, status=400)

    client_id, is_new = get_client_id(request)
    goal = get_object_or_404(Goal, id=goal_id)

    reaction, created = Reaction.objects.get_or_create(
        goal=goal,
        client_id=client_id,
        reaction_type=reaction_type,
    )
    if not created:
        reaction.delete()
        reacted = False
    else:
        reacted = True

    count = goal.reactions.filter(reaction_type=reaction_type).count()
    response = JsonResponse({'reacted': reacted, 'count': count})
    return _attach_client_cookie(response, client_id, is_new)
