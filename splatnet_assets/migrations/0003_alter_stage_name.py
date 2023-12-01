# Generated by Django 4.2.7 on 2023-12-01 00:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('splatnet_assets', '0002_alter_localizationstring_type_challenge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stage',
            name='name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    to='splatnet_assets.localizationstring'),
        ),
    ]
