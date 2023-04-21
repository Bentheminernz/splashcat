# Generated by Django 4.2 on 2023-04-21 02:59

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import splatnet_assets.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('splatnet_assets', '0006_stage_image_stage_image_banner_stage_internal_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Battle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('splatnet_id', models.CharField(max_length=32)),
                ('raw_data', models.JSONField()),
                ('data_type', models.CharField(max_length=32)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vs_mode', models.CharField(
                    choices=[('REGULAR', 'Regular'), ('LEAGUE', 'League'), ('FEST', 'Splatfest'),
                             ('BANKARA', 'Anarchy'), ('X_MATCH', 'X Battle')], max_length=32)),
                ('vs_rule', models.CharField(
                    choices=[('TURF_WAR', 'Turf War'), ('AREA', 'Splat Zones'), ('LOFT', 'Tower Control'),
                             ('CLAM', 'Clam Blitz'), ('GOAL', 'Rainmaker')], max_length=32)),
                ('played_time', models.DateTimeField()),
                ('duration', models.IntegerField()),
                ('judgement', models.CharField(
                    choices=[('WIN', 'Win'), ('LOSE', 'Lose'), ('DRAW', 'Draw'), ('EXEMPTED_LOSE', 'Lose (Exempted)'),
                             ('DEEMED_LOSE', 'Deemed Lose')], max_length=32)),
                ('player_npln_id', models.CharField(max_length=50)),
                ('player_name', models.CharField(max_length=50)),
                ('player_name_id', models.CharField(max_length=10)),
                ('player_paint',
                 models.IntegerField(null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('knockout',
                 models.CharField(blank=True, choices=[('NEITHER', 'Neither'), ('WIN', 'Win'), ('LOSE', 'Lose')],
                                  max_length=32, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_my_team', models.BooleanField()),
                ('color', splatnet_assets.fields.ColorField(max_length=8)),
                ('fest_streak_win_count', models.IntegerField(blank=True, null=True)),
                ('fest_team_name', models.CharField(blank=True, max_length=50, null=True)),
                ('fest_uniform_bonus_rate', models.FloatField(blank=True, null=True)),
                ('fest_uniform_name', models.CharField(blank=True, max_length=50, null=True)),
                ('judgement',
                 models.CharField(choices=[('WIN', 'Win'), ('LOSE', 'Lose'), ('DRAW', 'Draw')], max_length=32)),
                ('order', models.IntegerField()),
                ('noroshi', models.IntegerField(blank=True, null=True)),
                ('paint_ratio', models.FloatField(blank=True, null=True)),
                ('score', models.IntegerField(blank=True, null=True)),
                ('tricolor_role', models.CharField(blank=True,
                                                   choices=[('ATTACK1', 'Attack 1'), ('ATTACK2', 'Attack 2'),
                                                            ('DEFENSE', 'Defense')], max_length=32, null=True)),
                ('battle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams',
                                             to='battles.battle')),
            ],
        ),
        migrations.CreateModel(
            name='PlayerGear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gear', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='splatnet_assets.gear')),
                ('primary_ability', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                                      to='splatnet_assets.ability')),
                ('secondary_ability_1',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                   to='splatnet_assets.ability')),
                ('secondary_ability_2',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                   to='splatnet_assets.ability')),
                ('secondary_ability_3',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                   to='splatnet_assets.ability')),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_self', models.BooleanField()),
                ('npln_id', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=50)),
                ('name_id', models.CharField(max_length=10)),
                ('disconnect', models.BooleanField()),
                ('kills', models.IntegerField(blank=True, null=True)),
                ('assists', models.IntegerField(blank=True, null=True)),
                ('deaths', models.IntegerField(blank=True, null=True)),
                ('specials', models.IntegerField(blank=True, null=True)),
                ('paint', models.IntegerField(blank=True, null=True)),
                ('noroshi_try', models.IntegerField(blank=True, null=True)),
                ('clothing_gear', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                                       to='battles.playergear')),
                ('head_gear', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                                   to='battles.playergear')),
                ('nameplate_background', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                                           to='splatnet_assets.nameplatebackground')),
                ('nameplate_badge_1',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                   to='splatnet_assets.nameplatebadge')),
                ('nameplate_badge_2',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                   to='splatnet_assets.nameplatebadge')),
                ('nameplate_badge_3',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                   to='splatnet_assets.nameplatebadge')),
                ('shoes_gear', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                                    to='battles.playergear')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players',
                                           to='battles.team')),
                ('title_adjective',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='splatnet_assets.titleadjective')),
                ('title_subject',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='splatnet_assets.titlesubject')),
                ('weapon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                             to='splatnet_assets.weapon')),
            ],
        ),
        migrations.CreateModel(
            name='BattleAward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('award', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='splatnet_assets.award')),
                ('battle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='battles.battle')),
            ],
        ),
        migrations.AddField(
            model_name='battle',
            name='awards',
            field=models.ManyToManyField(related_name='battles', through='battles.BattleAward',
                                         to='splatnet_assets.award'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_clothing_gear',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                       to='battles.playergear'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_head_gear',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                       to='battles.playergear'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_nameplate_background',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    to='splatnet_assets.nameplatebackground'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_nameplate_badge_1',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                    to='splatnet_assets.nameplatebadge'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_nameplate_badge_2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                    to='splatnet_assets.nameplatebadge'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_nameplate_badge_3',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                    to='splatnet_assets.nameplatebadge'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_shoes_gear',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='+',
                                       to='battles.playergear'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_title_adjective',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='splatnet_assets.titleadjective'),
        ),
        migrations.AddField(
            model_name='battle',
            name='player_title_subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='splatnet_assets.titlesubject'),
        ),
        migrations.AddField(
            model_name='battle',
            name='uploader',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='battle',
            name='vs_stage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='splatnet_assets.stage'),
        ),
    ]
