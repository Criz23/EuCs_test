# Generated by Django 2.2.13 on 2021-08-01 06:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digest', '0003_auto_20210801_0630'),
    ]

    operations = [
        migrations.AddField(
            model_name='digest',
            name='tobeSend',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='digest',
            name='sent',
            field=models.BooleanField(default=False, editable=False, null=True),
        ),
    ]
