# Generated by Django 4.2.11 on 2025-04-08 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configurador', '0016_maquinavirtual_roles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maquinavirtual',
            name='roles',
            field=models.ManyToManyField(blank=True, null=True, to='configurador.rolansible'),
        ),
    ]
