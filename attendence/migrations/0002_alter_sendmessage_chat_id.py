# Generated by Django 4.2.16 on 2024-12-03 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendence', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sendmessage',
            name='chat_id',
            field=models.CharField(default=1, max_length=150),
            preserve_default=False,
        ),
    ]