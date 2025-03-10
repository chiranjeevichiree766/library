# Generated by Django 5.1.7 on 2025-03-08 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="groups",
            field=models.ManyToManyField(
                blank=True,
                related_name="customuser_groups",
                related_query_name="customuser",
                to="auth.group",
            ),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="user_permissions",
            field=models.ManyToManyField(
                blank=True,
                related_name="customuser_user_permissions",
                related_query_name="customuser",
                to="auth.permission",
            ),
        ),
    ]
