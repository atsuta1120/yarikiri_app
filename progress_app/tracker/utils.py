import uuid
from datetime import timedelta

from django.utils import timezone

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


def get_reset_hour(client_id):
    from .models import ClientSetting

    setting = ClientSetting.objects.filter(client_id=client_id).first()
    return setting.reset_hour if setting else 0


def get_today(client_id):
    """
    ユーザーにとっての「今日」の日付。
    リセット時刻（reset_hour）より前の時間帯は前日として扱う
    """
    now = timezone.localtime()
    return (now - timedelta(hours=get_reset_hour(client_id))).date()
