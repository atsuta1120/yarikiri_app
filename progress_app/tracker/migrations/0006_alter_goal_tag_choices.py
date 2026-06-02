from django.db import migrations, models

_VALID_TAGS = {'未分類', '学習', '健康', 'お金', '仕事', '生活改善', '趣味', '創作', '人間関係'}


def normalize_tags(apps, schema_editor):
    Goal = apps.get_model('tracker', 'Goal')
    for goal in Goal.objects.all():
        if goal.tag not in _VALID_TAGS:
            goal.tag = '未分類'
            goal.save(update_fields=['tag'])


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0005_goal_tag_reaction_goalview'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goal',
            name='tag',
            field=models.CharField(
                blank=True,
                choices=[
                    ('未分類', '未分類'),
                    ('学習', '学習'),
                    ('健康', '健康'),
                    ('お金', 'お金'),
                    ('仕事', '仕事'),
                    ('生活改善', '生活改善'),
                    ('趣味', '趣味'),
                    ('創作', '創作'),
                    ('人間関係', '人間関係'),
                ],
                default='未分類',
                max_length=50,
            ),
        ),
        migrations.RunPython(normalize_tags, migrations.RunPython.noop),
    ]
