# Generated by Django 2.2.13 on 2021-10-24 15:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0002_auto_20211024_1518'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resource',
            old_name='dateUpdated2',
            new_name='dateUpdated',
        ),
    ]
