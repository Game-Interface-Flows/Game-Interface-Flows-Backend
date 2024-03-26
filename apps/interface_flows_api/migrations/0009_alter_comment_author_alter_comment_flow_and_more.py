# Generated by Django 4.2.11 on 2024-03-25 19:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("interface_flows_api", "0008_alter_frame_flow"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_comments",
                to="interface_flows_api.profile",
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="flow",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="flow_comments",
                to="interface_flows_api.flow",
            ),
        ),
        migrations.AlterField(
            model_name="frame",
            name="frame",
            field=models.ImageField(upload_to="frames/"),
        ),
    ]