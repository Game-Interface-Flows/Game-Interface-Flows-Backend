# Generated by Django 4.2.11 on 2024-03-26 10:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "interface_flows_api",
            "0009_alter_comment_author_alter_comment_flow_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="profile_photo_url",
            field=models.ImageField(default="profile.png", upload_to="profiles/"),
        ),
    ]
