# Generated by Django 4.1.3 on 2022-11-05 11:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='surfer',
            options={'verbose_name_plural': 'Surfers'},
        ),
        migrations.RenameField(
            model_name='surfer',
            old_name='strava_id',
            new_name='strava_user_id',
        ),
        migrations.CreateModel(
            name='SurfSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strava_activity_id', models.CharField(max_length=90)),
                ('number_of_waves', models.IntegerField(default=0)),
                ('surfer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.surfer')),
            ],
        ),
    ]
