# Generated by Django 2.2.13 on 2021-08-06 07:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_auto_20210806_0641'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='last_name',
            new_name='surname',
        ),
    ]
