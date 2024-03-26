# Generated by Django 4.2.11 on 2024-03-21 21:01

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "interface_flows_api",
            "0002_rename_graph_frame_flow_alter_frame_position_x_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="flow",
            name="date",
            field=models.DateField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="flow",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="flow_author",
                to="interface_flows_api.profile",
            ),
        ),
    ]
