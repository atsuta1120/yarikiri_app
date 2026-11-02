import json
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import TestCase

from .models import ClientSetting, Goal
from .utils import CLIENT_ID_COOKIE, get_today

JST = ZoneInfo("Asia/Tokyo")
CLIENT_ID = "11111111-1111-1111-1111-111111111111"


def _jst(*args):
    return datetime(*args, tzinfo=JST)


class GetTodayTests(TestCase):
    def test_default_reset_hour_switches_at_midnight(self):
        with patch("django.utils.timezone.now", return_value=_jst(2026, 11, 2, 0, 30)):
            self.assertEqual(get_today(CLIENT_ID).isoformat(), "2026-11-02")

    def test_before_reset_hour_is_previous_day(self):
        ClientSetting.objects.create(client_id=CLIENT_ID, reset_hour=3)
        with patch("django.utils.timezone.now", return_value=_jst(2026, 11, 2, 2, 59)):
            self.assertEqual(get_today(CLIENT_ID).isoformat(), "2026-11-01")
        with patch("django.utils.timezone.now", return_value=_jst(2026, 11, 2, 3, 0)):
            self.assertEqual(get_today(CLIENT_ID).isoformat(), "2026-11-02")


class SettingsApiTests(TestCase):
    def setUp(self):
        self.client.cookies[CLIENT_ID_COOKIE] = CLIENT_ID

    def _put(self, body):
        return self.client.put("/api/settings/", json.dumps(body), content_type="application/json", secure=True)

    def test_get_returns_default(self):
        self.assertEqual(self.client.get("/api/settings/", secure=True).json(), {"reset_hour": 0})

    def test_put_saves_reset_hour(self):
        self.assertEqual(self._put({"reset_hour": 4}).json(), {"reset_hour": 4})
        self.assertEqual(self.client.get("/api/settings/", secure=True).json(), {"reset_hour": 4})

    def test_put_rejects_out_of_range(self):
        for value in [7, -1, "3", None, True]:
            self.assertEqual(self._put({"reset_hour": value}).status_code, 400)

    def test_goals_use_reset_hour(self):
        self._put({"reset_hour": 3})
        Goal.objects.create(client_id=CLIENT_ID, title="前日の目標", difficulty="small", weight=1, date="2026-11-01")
        with patch("django.utils.timezone.now", return_value=_jst(2026, 11, 2, 1, 0)):
            data = self.client.get("/api/goals/", secure=True).json()
        self.assertEqual(data["today"], "2026-11-01")
        self.assertEqual([g["title"] for g in data["goals"]], ["前日の目標"])
