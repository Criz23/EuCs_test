# Generated by Django 2.2.13 on 2021-08-01 05:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20210727_1511'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='keyword',
            options={'ordering': ['-id']},
        ),
    ]
