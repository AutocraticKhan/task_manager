# Generated by Django 5.1.6 on 2025-03-16 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("task_manager", "0003_task_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="subtask",
            name="completed",
            field=models.BooleanField(default=False),
        ),
    ]
