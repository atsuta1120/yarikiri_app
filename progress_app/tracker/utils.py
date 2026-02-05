import uuid

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
