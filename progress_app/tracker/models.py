from django.db import models


class Goal(models.Model):
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

    client_id = models.CharField(max_length=36, db_index=True, null=True, blank=True)

    tag = models.CharField(max_length=50, blank=True, default='未分類')


class Reaction(models.Model):
    REACTION_CHOICES = [
        ('fire', '🔥'),
        ('clap', '👏'),
        ('muscle', '💪'),
    ]

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='reactions')
    client_id = models.CharField(max_length=36, db_index=True)
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('goal', 'client_id', 'reaction_type')


class GoalView(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='views')
    client_id = models.CharField(max_length=36, db_index=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('goal', 'client_id')
