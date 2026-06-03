import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Goal, GoalView, Reaction
from .utils import CLIENT_ID_COOKIE, get_client_id

_VALID_TAGS = {choice[0] for choice in Goal.TAG_CHOICES}
_VALID_DIFFICULTIES = {"small", "medium", "large"}
_WEIGHT_MAP = {"small": 1, "medium": 3, "large": 5}
_REACTION_EMOJI = {"fire": "🔥", "clap": "👏", "muscle": "💪"}
_WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _attach_cookie(response, client_id, is_new):
    if is_new:
        response.set_cookie(
            CLIENT_ID_COOKIE,
            client_id,
            max_age=60 * 60 * 24 * 365,
            samesite="None",
            httponly=True,
            secure=True,
        )
    return response


def _goal_to_dict(goal, client_id=None):
    reaction_counts = {}
    for rtype, emoji in _REACTION_EMOJI.items():
        count = goal.reactions.filter(reaction_type=rtype).count()
        reacted = False
        if client_id:
            reacted = goal.reactions.filter(reaction_type=rtype, client_id=client_id).exists()
        reaction_counts[rtype] = {"emoji": emoji, "count": count, "reacted": reacted}

    return {
        "id": goal.id,
        "title": goal.title,
        "difficulty": goal.difficulty,
        "weight": goal.weight,
        "is_done": goal.is_done,
        "tag": goal.tag,
        "date": goal.date.isoformat(),
        "created_at": goal.created_at.isoformat(),
        "view_count": goal.views.count(),
        "reaction_counts": reaction_counts,
        "is_mine": goal.client_id == client_id if client_id else None,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def goals(request):
    client_id, is_new = get_client_id(request)
    today = timezone.localdate()

    if request.method == "GET":
        goal_list = Goal.objects.filter(client_id=client_id, date=today).order_by("-created_at")
        total_weight = sum(g.weight for g in goal_list)
        done_weight = sum(g.weight for g in goal_list if g.is_done)
        progress = 0 if total_weight == 0 else int(done_weight / total_weight * 100)

        data = {
            "today": today.isoformat(),
            "today_str": f"{today.year}年{today.month}月{today.day}日（{_WEEKDAY_JA[today.weekday()]}）",
            "progress_percent": progress,
            "total_weight": total_weight,
            "done_weight": done_weight,
            "goals": [_goal_to_dict(g, client_id) for g in goal_list],
        }
        response = JsonResponse(data)
        return _attach_cookie(response, client_id, is_new)

    # POST
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title = (body.get("title") or "").strip()
    difficulty = body.get("difficulty")
    tag = body.get("tag") or "未分類"

    if not title:
        return JsonResponse({"error": "タイトルを入力してください"}, status=400)
    if difficulty not in _VALID_DIFFICULTIES:
        return JsonResponse({"error": "難易度が不正です"}, status=400)
    if tag not in _VALID_TAGS:
        tag = "未分類"

    goal = Goal.objects.create(
        client_id=client_id,
        title=title,
        difficulty=difficulty,
        weight=_WEIGHT_MAP[difficulty],
        is_done=False,
        date=today,
        tag=tag,
    )
    response = JsonResponse(_goal_to_dict(goal, client_id), status=201)
    return _attach_cookie(response, client_id, is_new)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def goal_detail(request, goal_id):
    client_id, is_new = get_client_id(request)
    try:
        goal = Goal.objects.get(id=goal_id, client_id=client_id)
    except Goal.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method == "DELETE":
        goal.delete()
        response = JsonResponse({"deleted": True})
        return _attach_cookie(response, client_id, is_new)

    # PUT
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title = (body.get("title") or "").strip()
    difficulty = body.get("difficulty")
    tag = body.get("tag") or "未分類"

    if not title:
        return JsonResponse({"error": "タイトルを入力してください"}, status=400)
    if difficulty not in _VALID_DIFFICULTIES:
        return JsonResponse({"error": "難易度が不正です"}, status=400)
    if tag not in _VALID_TAGS:
        tag = "未分類"

    goal.title = title
    goal.difficulty = difficulty
    goal.weight = _WEIGHT_MAP[difficulty]
    goal.tag = tag
    goal.save(update_fields=["title", "difficulty", "weight", "tag"])

    response = JsonResponse(_goal_to_dict(goal, client_id))
    return _attach_cookie(response, client_id, is_new)


@csrf_exempt
@require_http_methods(["POST"])
def toggle_goal(request, goal_id):
    client_id, is_new = get_client_id(request)
    try:
        goal = Goal.objects.get(id=goal_id, client_id=client_id)
    except Goal.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    goal.is_done = not goal.is_done
    goal.save(update_fields=["is_done"])

    response = JsonResponse({"id": goal.id, "is_done": goal.is_done})
    return _attach_cookie(response, client_id, is_new)


@require_http_methods(["GET"])
def timeline_api(request, tag):
    client_id, is_new = get_client_id(request)
    today = timezone.localdate()

    if tag not in _VALID_TAGS:
        return JsonResponse({"error": "Invalid tag"}, status=400)

    goal_list = Goal.objects.filter(tag=tag, date=today).order_by("-created_at")

    for goal in goal_list:
        if goal.client_id != client_id:
            GoalView.objects.get_or_create(goal=goal, client_id=client_id)

    data = {
        "tag": tag,
        "today_str": f"{today.year}年{today.month}月{today.day}日（{_WEEKDAY_JA[today.weekday()]}）",
        "goals": [_goal_to_dict(g, client_id) for g in goal_list],
    }
    response = JsonResponse(data)
    return _attach_cookie(response, client_id, is_new)


@csrf_exempt
@require_http_methods(["POST"])
def react_goal_api(request, goal_id, reaction_type):
    if reaction_type not in _REACTION_EMOJI:
        return JsonResponse({"error": "invalid reaction"}, status=400)

    client_id, is_new = get_client_id(request)
    try:
        goal = Goal.objects.get(id=goal_id)
    except Goal.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    reaction, created = Reaction.objects.get_or_create(
        goal=goal, client_id=client_id, reaction_type=reaction_type
    )
    if not created:
        reaction.delete()
        reacted = False
    else:
        reacted = True

    count = goal.reactions.filter(reaction_type=reaction_type).count()
    response = JsonResponse({"reacted": reacted, "count": count})
    return _attach_cookie(response, client_id, is_new)


@require_http_methods(["GET"])
def history_api(request):
    client_id, is_new = get_client_id(request)
    today = timezone.localdate()

    past_goals = Goal.objects.filter(client_id=client_id, date__lt=today).order_by("-date", "-created_at")

    from collections import defaultdict
    days = defaultdict(list)
    for goal in past_goals:
        days[goal.date].append(goal)

    history_list = []
    for date in sorted(days.keys(), reverse=True):
        day_goals = days[date]
        total = sum(g.weight for g in day_goals)
        done = sum(g.weight for g in day_goals if g.is_done)
        progress = 0 if total == 0 else int(done / total * 100)
        history_list.append({
            "date": date.isoformat(),
            "date_str": f"{date.year}年{date.month}月{date.day}日（{_WEEKDAY_JA[date.weekday()]}）",
            "progress": progress,
            "goals": [_goal_to_dict(g, client_id) for g in day_goals],
        })

    response = JsonResponse({"history": history_list})
    return _attach_cookie(response, client_id, is_new)


@require_http_methods(["GET"])
def tag_choices_api(request):
    response = JsonResponse({"tags": [{"value": v, "label": l} for v, l in Goal.TAG_CHOICES]})
    return response
