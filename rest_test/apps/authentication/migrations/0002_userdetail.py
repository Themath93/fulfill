# Generated by Django 3.2.16 on 2023-03-05 21:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subinventory', models.CharField(blank=True, max_length=150)),
                ('contact_number_1', models.CharField(blank=True, max_length=150)),
                ('contact_number_2', models.CharField(blank=True, max_length=150)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('postcode', models.CharField(blank=True, max_length=150)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
