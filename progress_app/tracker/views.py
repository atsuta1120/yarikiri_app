import os,base64,json
from datetime import date, datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Goal
import uuid


@csrf_exempt  # 学習用：ローカル限定で CSRF 無効化
def save_screenshot(request):
    """
    フロントから送られてきた画像データを
    日付＋時間つきのファイル名で保存するビュー
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    # JSON を読む
    data = json.loads(request.body.decode("utf-8"))
    data_url = data.get("image")

    # "data:image/png;base64,xxxxx" を分解
    header, encoded = data_url.split(",", 1)
    image_data = base64.b64decode(encoded)

    # 保存先フォルダ（プロジェクト直下 /screenshots）
    save_dir = os.path.join(settings.BASE_DIR, "screenshots")
    os.makedirs(save_dir, exist_ok=True)

    # ---------- ★ここが追加・変更ポイント ----------
    # ファイル名：progress_YYYY-MM-DD_HH-MM-SS.png
    now = datetime.now()
    filename = now.strftime("progress_%Y-%m-%d_%H-%M-%S.png")
    # ---------------------------------------------

    filepath = os.path.join(save_dir, filename)

    # ファイルとして保存
    with open(filepath, "wb") as f:
        f.write(image_data)

    return JsonResponse({"status": "ok", "filename": filename})


def toggle_done(request, goal_id):
    """
    目標の達成状態（is_done）を ON / OFF 切り替える
    """
    goal = get_object_or_404(Goal, id=goal_id)
    goal.is_done = not goal.is_done
    goal.save()
    return redirect("tracker:home")




def home(request):
    today = date.today()

    client_id, is_new = get_client_id(request)

    goals = Goal.objects.filter(client_id=client_id, date=today)

    total_weight = sum(goal.weight for goal in goals)
    done_weight = sum(goal.weight for goal in goals if goal.is_done)

    if total_weight > 0:
        progress_percent = int((done_weight / total_weight) * 100)
    else:
        progress_percent = 0

    context = {
        "goals": goals,
        "progress_percent": progress_percent,
    }

    response = render(request, "tracker/home.html", context)

    # Cookieが無かった場合だけセット
    if is_new:
        response.set_cookie(
            CLIENT_ID_COOKIE,
            client_id,
            max_age=60 * 60 * 24 * 365,  # 1年
            samesite="Lax",
        )

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
            user=User.objects.first(),  # ここは今まで通り（将来ログイン導入で消す）
            title=title,
            difficulty=difficulty,
            weight=weight,
            is_done=False,
            date=date.today(),
        )

        response = redirect("tracker:home")
        if is_new:
            response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60*60*24*365, samesite="Lax")
        return response

    response = render(request, "tracker/add_goal.html")
    if is_new:
        response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60*60*24*365, samesite="Lax")
    return response

def toggle_done(request, goal_id):
    client_id, is_new = get_client_id(request)

    goal = get_object_or_404(Goal, id=goal_id, client_id=client_id)
    goal.is_done = not goal.is_done
    goal.save()

    response = redirect("tracker:home")
    if is_new:
        response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60*60*24*365, samesite="Lax")
    return response


def delete_goal(request, goal_id):
    client_id, is_new = get_client_id(request)

    goal = get_object_or_404(Goal, id=goal_id, client_id=client_id)
    goal.delete()

    response = redirect("tracker:home")
    if is_new:
        response.set_cookie(CLIENT_ID_COOKIE, client_id, max_age=60*60*24*365, samesite="Lax")
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
