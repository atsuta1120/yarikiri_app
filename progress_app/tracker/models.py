from django.db import models
from django.contrib.auth.models import User


class Goal(models.Model):
    """
    1つの「目標」を表すモデル。
    ユーザーが日ごとに自由に作成し、
    難易度に応じた重みを持つ。
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    DIFFICULTY_CHOICES = [
        ('small', '小'),
        ('medium', '中'),
        ('large', '大'),
    ]

    title = models.CharField(max_length=255)

    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
    )

    # 小=1 / 中=3 / 大=5 を保持するカラム
    weight = models.IntegerField()

    is_done = models.BooleanField(default=False)

    # 「この目標は何日分か」を表す日付
    date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    # TODO: 必要なら __str__ を実装（タイトルを返すなど）
